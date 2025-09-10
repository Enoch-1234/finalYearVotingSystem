# votingSystem/admin.py
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from .models import Block, Category, Candidate
import hashlib

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('index', 'timestamp', 'hash', 'previous_hash', 'verify_status')
    search_fields = ('hash', 'previous_hash')
    readonly_fields = ('index', 'timestamp', 'hash', 'previous_hash', 'vote_data')
    ordering = ('-timestamp',)
    list_per_page = 25
    actions = ['verify_blockchain']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'verify-blockchain/',
                self.admin_site.admin_view(
                    permission_required('votingSystem.can_verify_blockchain')(self.verify_blockchain_view)
                ),
                name='verify_blockchain',
            ),
        ]
        return custom_urls + urls

    def _verify_blockchain(self):
        blocks = Block.objects.order_by('index')
        results = []
        previous_block = None

        for block in blocks:
            # Format timestamp consistently
            timestamp_str = block.timestamp.strftime('%Y-%m-%d %H:%M:%S+00:00')
            block_data = f"{block.index}{timestamp_str}{block.vote_data}{block.previous_hash}"
            calculated_hash = hashlib.sha256(block_data.encode()).hexdigest()
            hash_valid = calculated_hash == block.hash

            previous_hash_valid = True
            if previous_block:
                previous_hash_valid = block.previous_hash == previous_block.hash
            elif block.index == 1:
                previous_hash_valid = block.previous_hash == '0' * 64

            status = 'Valid'
            errors = []
            if not hash_valid:
                status = 'Invalid'
                errors.append(f'Hash mismatch (calculated: {calculated_hash})')
            if not previous_hash_valid:
                status = 'Invalid'
                errors.append('Previous hash mismatch')

            results.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'status': status,
                'errors': errors,
                'calculated_hash': calculated_hash if not hash_valid else None,
            })

            previous_block = block

        return results

    def verify_blockchain(self, request, queryset=None):
        verification_results = self._verify_blockchain()
        if all(result['status'] == 'Valid' for result in verification_results):
            self.message_user(request, "Blockchain verification successful: All blocks are valid.", level=messages.SUCCESS)
        else:
            self.message_user(
                request,
                "Blockchain verification failed: Some blocks are invalid. See detailed results.",
                level=messages.ERROR
            )
        context = {
            'results': verification_results,
            'title': 'Blockchain Verification Results',
        }
        return render(request, 'block/verify_blockchain.html', context)

    verify_blockchain.short_description = "Verify blockchain integrity"

    def verify_blockchain_view(self, request):
        return self.verify_blockchain(request)

    def verify_status(self, obj):
        timestamp_str = obj.timestamp.strftime('%Y-%m-%d %H:%M:%S+00:00')
        block_data = f"{obj.index}{timestamp_str}{obj.vote_data}{obj.previous_hash}"
        calculated_hash = hashlib.sha256(block_data.encode()).hexdigest()
        hash_valid = calculated_hash == obj.hash
        previous_block = Block.objects.filter(index=obj.index - 1).first()
        previous_hash_valid = (
            (previous_block and obj.previous_hash == previous_block.hash)
            or (obj.index == 1 and obj.previous_hash == '0' * 64)
        )
        if hash_valid and previous_hash_valid:
            return format_html('<span style="color: green;">Valid</span>')
        return format_html('<span style="color: red;">Invalid</span>')
    verify_status.short_description = 'Verification Status'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('eligible_departments',)

@admin.register(Candidate)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_display')
    search_fields = ('name',)
    list_filter = ('category',)
    readonly_fields = ('photo_preview',)

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="300" height="300" style="object-fit: cover; border-radius: 4px;" />',
                obj.photo.url
            )
        return "No Image"
    photo_preview.short_description = 'Photo'

    def category_display(self, obj):
        return obj.category.name
    category_display.short_description = 'Category'