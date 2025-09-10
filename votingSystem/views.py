# votingSystem/views.py
import json
import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from .models import Block, Category, Candidate
from account.models import Student
from django.utils import timezone
from datetime import datetime

def index(request):
    if not request.user.is_authenticated:
        return redirect('student_login')

    if hasattr(request.user, 'staff_profile'):
        return redirect('results')

    try:
        student = request.user.student_profile
        if student.has_voted:
            messages.info(request, "You have already voted.")
            return redirect('results')
        categories = Category.objects.filter(eligible_departments__in=[student.department])
        return render(request, 'dashboard.html', {'categories': categories})
    except Student.DoesNotExist:
        messages.error(request, "No student profile found for this user.")
        return redirect('student_login')

@login_required
def vote(request):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can vote.")
        return redirect('index')

    student = request.user.student_profile
    if student.has_voted:
        messages.info(request, "You have already voted.")
        return redirect('results')

    if request.method == 'POST':
        cipher = Fernet(settings.FERNET_KEY)
        previous_block = Block.objects.order_by('-index').first()
        previous_hash = previous_block.hash if previous_block else '0' * 64

        votes = {}
        for key, value in request.POST.items():
            if key.startswith('category-'):
                category_id = int(key.split('-')[1])
                candidate_id = int(value)
                category = Category.objects.get(id=category_id)
                if student.department not in category.eligible_departments.all():
                    messages.error(request, f"You are not eligible to vote in {category.name}.")
                    return redirect('index')
                votes[category_id] = candidate_id

        vote_data = json.dumps(votes)
        encrypted_vote = cipher.encrypt(vote_data.encode()).decode()

        index = previous_block.index + 1 if previous_block else 1
        timestamp = timezone.now()
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S+00:00')
        block_data = f"{index}{timestamp_str}{encrypted_vote}{previous_hash}"
        block_hash = hashlib.sha256(block_data.encode()).hexdigest()

        Block.objects.create(
            index=index,
            timestamp=timestamp,
            vote_data=encrypted_vote,
            previous_hash=previous_hash,
            hash=block_hash
        )

        student.has_voted = True
        student.save()

        cache.delete('vote_counts')

        # Store vote data in session for one-time confirmation
        request.session['vote_confirmation'] = {
            'encrypted_vote': encrypted_vote,
            'block_hash': block_hash,
            'timestamp': timestamp_str
        }
        request.session['vote_confirmation_accessed'] = False

        return redirect('vote_confirmation')

    return redirect('index')

@login_required
def vote_confirmation(request):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access this page.")
        return redirect('index')

    if request.session.get('vote_confirmation_accessed', True):
        messages.error(request, "Vote confirmation is only available once immediately after voting.")
        return redirect('results')

    vote_confirmation = request.session.get('vote_confirmation')
    if not vote_confirmation:
        messages.error(request, "No vote confirmation data available.")
        return redirect('results')

    if request.method == 'POST':
        if 'download' in request.POST:
            content = (
                f"Vote Confirmation\n"
                f"Timestamp: {vote_confirmation['timestamp']}\n"
                f"Encrypted Vote: {vote_confirmation['encrypted_vote']}\n"
                f"Block Hash: {vote_confirmation['block_hash']}\n"
            )
            response = HttpResponse(content, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="vote_confirmation.txt"'
            # Mark as accessed and clear session
            request.session['vote_confirmation_accessed'] = True
            del request.session['vote_confirmation']
            request.session.modified = True
            return response

    # Mark as accessed after rendering
    request.session['vote_confirmation_accessed'] = True
    request.session.modified = True
    context = {
        'encrypted_vote': vote_confirmation['encrypted_vote'],
        'block_hash': vote_confirmation['block_hash'],
        'timestamp': vote_confirmation['timestamp']
    }
    return render(request, 'vote_confirmation.html', context)

@login_required
def verify_vote(request):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can verify votes.")
        return redirect('index')

    if request.method == 'POST':
        input_value = request.POST.get('vote_input', '').strip()
        if not input_value:
            messages.error(request, "Please provide an encrypted vote or block hash.")
            return render(request, 'verify_vote.html')

        # Check if input is an encrypted vote or hash
        block = None
        if len(input_value) == 64 and all(c in '0123456789abcdef' for c in input_value.lower()):
            # Likely a hash
            try:
                block = Block.objects.get(hash=input_value)
            except Block.DoesNotExist:
                pass
        else:
            # Likely encrypted vote
            try:
                block = Block.objects.get(vote_data=input_value)
            except Block.DoesNotExist:
                pass

        if block:
            # Verify block integrity
            timestamp_str = block.timestamp.strftime('%Y-%m-%d %H:%M:%S+00:00')
            previous_block = Block.objects.filter(index=block.index - 1).first()
            previous_hash = previous_block.hash if previous_block else '0' * 64
            block_data = f"{block.index}{timestamp_str}{block.vote_data}{previous_hash}"
            calculated_hash = hashlib.sha256(block_data.encode()).hexdigest()
            is_valid = calculated_hash == block.hash
            context = {
                'block': {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'hash': block.hash,
                    'is_valid': is_valid
                }
            }
            if is_valid:
                messages.success(request, "Vote verified successfully: The vote is valid and untampered.")
            else:
                messages.error(request, "Vote verification failed: The vote has been tampered with.")
            return render(request, 'verify_vote.html', context)
        else:
            messages.error(request, "No matching vote or block found.")
            return render(request, 'verify_vote.html')

    return render(request, 'verify_vote.html')

@login_required
def results(request):
    # Check access: students who have voted or staff
    try:
        student = request.user.student_profile
        if not student.has_voted and not request.user.is_staff:
            messages.error(request, "You must vote to view results.")
            return redirect('index')
    except Student.DoesNotExist:
        if not request.user.is_staff:
            messages.error(request, "Only students who have voted or staff can view results.")
            return redirect('student_login')

    # Initialize Fernet cipher
    cipher = Fernet(settings.FERNET_KEY)

    # Check cache for vote counts
    cache_key = 'vote_counts'
    vote_counts = cache.get(cache_key)
    if not vote_counts:
        vote_counts = {}
        for block in Block.objects.all():
            try:
                decrypted_data = cipher.decrypt(block.vote_data.encode()).decode()
                votes = json.loads(decrypted_data)
                for category_id, candidate_id in votes.items():
                    category_id = int(category_id)
                    candidate_id = int(candidate_id)
                    if category_id not in vote_counts:
                        vote_counts[category_id] = {}
                    vote_counts[category_id][candidate_id] = vote_counts[category_id].get(candidate_id, 0) + 1
            except Exception as e:
                print(f"Decryption error for block {block.index}: {e}")
                continue
        cache.set(cache_key, vote_counts, timeout=3600)  # Cache for 1 hour

    # Get search query
    search_query = request.GET.get('q', '').strip().lower()

    # Get categories and candidates
    categories = Category.objects.all()

    # Prepare results data
    results = []
    total_votes = {}

    for category in categories:
        # Calculate total votes for the category
        total_votes[category.id] = sum(vote_counts.get(category.id, {}).values())

        category_data = {
            'name': category.name,
            'candidates': []
        }
        candidates = category.candidate_set.all()

        for candidate in candidates:
            vote_count = vote_counts.get(category.id, {}).get(candidate.id, 0)
            percentage = (vote_count / total_votes[category.id] * 100) if total_votes[category.id] > 0 else 0
            category_data['candidates'].append({
                'name': candidate.name,
                'photo': candidate.photo.url,
                'votes': vote_count,
                'percentage': percentage
            })

        if category_data['candidates']:
            results.append(category_data)

    # Prepare search results (separate from main results)
    search_results = []
    if search_query:
        for category in categories:
            candidates = category.candidate_set.filter(name__icontains=search_query)
            for candidate in candidates:
                vote_count = vote_counts.get(category.id, {}).get(candidate.id, 0)
                search_results.append({
                    'name': candidate.name,
                    'category_name': category.name,
                    'votes': vote_count
                })

    # Current timestamp
    current_time = datetime.now(timezone.get_current_timezone()).strftime("%B %d, %Y, %I:%M %p GMT")

    return render(request, 'results.html', {
        'results': results,
        'search_results': search_results,
        'search_query': search_query,
        'current_time': current_time
    })