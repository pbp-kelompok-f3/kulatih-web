from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommunityCreateForm, MessageForm
from .models import Community, Membership, Message

# COMMUNITY MAIN PAGE
def community_home(request):
    q = request.GET.get('q', '').strip()
    communities = Community.objects.all()
    if q:
        communities = communities.filter(
            Q(name__icontains=q) |
            Q(short_description__icontains=q) |
            Q(full_description__icontains=q)
        )

    # list yg sudah di join user 
    joined_ids = set()
    if request.user.is_authenticated:
        joined_ids = set(
            Membership.objects.filter(user=request.user).values_list('community_id', flat=True)
        )
    return render(request, 'community/main_community.html', {
        'communities': communities,
        'q': q,
        'joined_ids': joined_ids,
    })


# CREATE COMMUNITY (otomatis kalo create = admin)
#@login_required
def community_create(request):
    if request.method == 'POST':
        form = CommunityCreateForm(request.POST)
        if form.is_valid():
            community = form.save(user=request.user)

            # buat membership admin
            Membership.objects.get_or_create(
                community=community, user=request.user,
                defaults={'role': 'admin'}
            )
            messages.success(request, 'Community berhasil dibuat.')
            return redirect('community:detail', slug=community.slug)
    else:
        form = CommunityCreateForm()
    return render(request, 'community/create.html', {'form': form})


# COMMUNITY DETAIL (info lengkap + tombol Join Us)
def community_detail(request, slug):
    c = get_object_or_404(Community, slug=slug)
    is_member = False
    if request.user.is_authenticated:
        is_member = Membership.objects.filter(user=request.user, community=c).exists()
    return render(request, 'community/detail.html', {
        'community': c,
        'is_member': is_member,
        'members_count': c.members_count(),
    })


# JOIN (tambah membership, otomatis hitung, add ke My Community List)
#@login_required
def join_community(request, slug):
    c = get_object_or_404(Community, slug=slug)
    mem, created = Membership.objects.get_or_create(community=c, user=request.user, defaults={'role': 'user'})
    if created:
        messages.success(request, f'Kamu bergabung di {c.name}.')
    else:
        messages.info(request, f'Kamu sudah menjadi anggota {c.name}.')
    return redirect('community:my_list')


# MY COMMUNITY LIST (daftar komunitas yang di join)
#@login_required
def my_community_list(request):
    memberships = Membership.objects.filter(user=request.user).select_related('community').order_by('joined_at')
    return render(request, 'community/my_list.html', {'memberships': memberships})


# LEAVE (hapus membership, balikin ke Community main)
#@login_required
def leave_community(request, slug):
    c = get_object_or_404(Community, slug=slug)
    Membership.objects.filter(user=request.user, community=c).delete()
    messages.success(request, f'Kamu keluar dari {c.name}.')
    return redirect('community:home')


# MY COMMUNITY GROUP (group chat)
#@login_required
def my_community_group(request, slug):
    c = get_object_or_404(Community, slug=slug)
    # hanya anggota yang boleh kirim/lihat chat
    if not Membership.objects.filter(user=request.user, community=c).exists():
        messages.error(request, 'Kamu harus bergabung terlebih dahulu.')
        return redirect('community:detail', slug=slug)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.community = c
            msg.sender = request.user
            msg.save()
            return redirect('community:my_group', slug=slug)  # PRG pattern
    else:
        form = MessageForm()

    messages_qs = c.messages.select_related('sender')
    return render(request, 'community/group.html', {
        'community': c,
        'form': form,
        'messages': messages_qs,
    })
