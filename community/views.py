from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommunityCreateForm, MessageForm
from .models import Community, Membership, Message
from django.http import JsonResponse
import json

# COMMUNITY MAIN PAGE
def community_home(request):
    q = request.GET.get('q', '').strip()
    communities = Community.objects.all()

    if request.user.is_authenticated:
        joined_ids = set(
            Membership.objects.filter(user=request.user).values_list('community_id', flat=True)
        )
        communities = communities.exclude(id__in=joined_ids)  # 🔥 sembunyikan yang sudah dijoin
    else:
        joined_ids = set()

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
@login_required
def community_create(request):
    if request.method == 'POST':
        form = CommunityCreateForm(request.POST)
        print(f"=== DEBUG CREATE COMMUNITY ===")
        print(f"POST data: {request.POST}")
        print(f"Form valid: {form.is_valid()}")
        
        if form.is_valid():
            print(f"Cleaned data: {form.cleaned_data}")
            try:
                community = form.save(user=request.user)
                print(f"Community created successfully!")
                print(f"ID: {community.id}")
                print(f"Name: {community.name}")
                print(f"Profile URL: {community.profile_image_url}")
                
                # Otomatis gabung sebagai admin
                Membership.objects.get_or_create(
                    community=community,
                    user=request.user,
                    defaults={'role': 'admin'}
                )
                
                messages.success(request, f'Community "{community.name}" berhasil dibuat!')
                return redirect('community:my_list')
            except Exception as e:
                print(f"ERROR saat save: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error: {str(e)}')
        else:
            print(f"Form TIDAK valid!")
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CommunityCreateForm()

    return render(request, 'community/create.html', {'form': form})



# COMMUNITY DETAIL (info lengkap + tombol Join Us)
def community_detail(request, id):
    c = get_object_or_404(Community, id=id)
    is_member = False
    if request.user.is_authenticated:
        is_member = Membership.objects.filter(user=request.user, community=c).exists()
    return render(request, 'community/detail.html', {
        'community': c,
        'is_member': is_member,
        'members_count': c.members_count(),
    })



# JOIN (tambah membership, otomatis hitung, add ke My Community List)
@login_required
def join_community(request, id):
    c = get_object_or_404(Community, id=id)
    mem, created = Membership.objects.get_or_create(community=c, user=request.user, defaults={'role': 'user'})
    if created:
        messages.success(request, f'Kamu bergabung di {c.name}.')
    else:
        messages.info(request, f'Kamu sudah menjadi anggota {c.name}.')
    return redirect('community:my_list')


# MY COMMUNITY LIST (daftar komunitas yang di join)
@login_required
def my_community_list(request):
    memberships = Membership.objects.filter(user=request.user).select_related('community').order_by('joined_at')
    return render(request, 'community/my_list.html', {'memberships': memberships})


# LEAVE (hapus membership, balikin ke Community main)
@login_required
def leave_community(request, id):
    c = get_object_or_404(Community, id=id)
    Membership.objects.filter(user=request.user, community=c).delete()
    messages.success(request, f'Kamu keluar dari {c.name}.')
    return redirect('community:home')


# MY COMMUNITY GROUP (group chat)
@login_required
def my_community_group(request, id):
    c = get_object_or_404(Community, id=id)
    if not Membership.objects.filter(user=request.user, community=c).exists():
        messages.error(request, 'Kamu harus bergabung terlebih dahulu.')
        return redirect('community:detail', id=id)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.community = c
            msg.sender = request.user
            msg.save()
            return redirect('community:my_group', id=id)

    else:
        form = MessageForm()

    messages_qs = c.messages.select_related('sender')
    return render(request, 'community/group.html', {
        'community': c,
        'form': form,
        'messages': messages_qs,
    })


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Community, Message

@login_required
def send_message_ajax(request, id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        community = get_object_or_404(Community, pk=id)
        msg = Message.objects.create(community=community, sender=request.user, text=text)
        
        return JsonResponse({
            'id': msg.id,
            'text': msg.text,
            'sender': msg.sender.username,
            'community_id': community.id,  
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)



@login_required
def edit_message(request, id, msg_id):
    """Edit pesan"""
    message = get_object_or_404(Message, id=msg_id, sender=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            messages.success(request, "Pesan berhasil diperbarui.")
            return redirect('community:my_group', id=id)
    else:
        form = MessageForm(instance=message)
    return render(request, 'community/edit_message.html', {'form': form, 'community': message.community})


@login_required
def delete_message(request, id, msg_id):
    """Hapus pesan via AJAX"""
    if request.method == 'DELETE':
        message = get_object_or_404(Message, id=msg_id, sender=request.user)
        message.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

