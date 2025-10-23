from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from .models import ForumPost

def is_admin(user):
    return user.is_staff or user.is_superuser

# USER VIEWS
def post_list(request):
    posts = ForumPost.objects.all().order_by('-created_at')
    return render(request, 'forum/post_list.html', {'posts': posts})

@login_required
def create_post(request):
    """Menambahkan posting baru"""
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')

        if not content:
            messages.error(request, "Isi postingan tidak boleh kosong.")
            return redirect('forum:create_post')

        ForumPost.objects.create(
            author=request.user,
            content=content,
            image=image,
            created_at=timezone.now()
        )
        messages.success(request, "Postingan berhasil dibuat!")
        return redirect('forum:post_list')

    return render(request, 'forum/create_post.html')

@login_required
def like_post(request, post_id):
    """Menambah like pada posting"""
    post = get_object_or_404(ForumPost, id=post_id)
    post.like_post()
    messages.success(request, f"Kamu menyukai postingan {post.author.username}.")
    return redirect('forum:post_list')

# ADMIN VIEWS
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Halaman admin custom untuk melihat dan kelola semua posting"""
    posts = ForumPost.objects.select_related('author').order_by('-created_at')
    return render(request, 'forum/admin_dashboard.html', {'posts': posts})


@user_passes_test(is_admin)
def delete_post(request, post_id):
    """Hapus posting dari dashboard admin custom"""
    post = get_object_or_404(ForumPost, id=post_id)
    post.delete()
    messages.success(request, "Postingan berhasil dihapus.")
    return redirect('forum:admin_dashboard')