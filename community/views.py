from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommunityCreateForm, MessageForm
from .models import Community, Membership, Message
from django.http import JsonResponse
import json
from django.urls import reverse
from django.core.paginator import Paginator


# COMMUNITY MAIN PAGE
def community_home(request):
    q = request.GET.get('q', '').strip()
    communities = Community.objects.all()

    # Filter komunitas yang belum dijoin
    if request.user.is_authenticated:
        joined_ids = set(
            Membership.objects.filter(user=request.user).values_list('community_id', flat=True)
        )
        communities = communities.exclude(id__in=joined_ids)
    else:
        joined_ids = set()

    # Pencarian
    if q:
        communities = communities.filter(
            Q(name__icontains=q) |
            Q(short_description__icontains=q) |
            Q(full_description__icontains=q)
        )

    # Pagination — tampil 6 per halaman
    paginator = Paginator(communities, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'community/main_community.html', {
        'communities': page_obj,
        'q': q,
        'joined_ids': joined_ids,
    })


@login_required
def community_create(request):
    if request.method == 'POST':
        form = CommunityCreateForm(request.POST)
        if form.is_valid():
            community = form.save(user=request.user)

            # Otomatis user jadi admin di komunitas baru
            Membership.objects.get_or_create(
                community=community,
                user=request.user,
                defaults={'role': 'admin'}
            )

            # Redirect ke my_list dengan parameter untuk toast
            return redirect(reverse('community:my_list') + '?created=true')
        else:
            messages.error(request, "Please correct the errors below.")
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
        messages.success(request, f'You have joined {c.name}.')
    else:
        messages.info(request, f'You are already a member of {c.name}.')
    return redirect('community:my_list')


# MY COMMUNITY LIST (daftar komunitas yang di join)
@login_required
def my_community_list(request):
    memberships = Membership.objects.filter(
        user=request.user
    ).select_related('community').order_by('joined_at')

    # aktifkan pagination
    paginator = Paginator(memberships, 6)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'community/my_list.html', {'memberships': page_obj})



# LEAVE (hapus membership, balikin ke Community main)
@login_required
def leave_community(request, id):
    c = get_object_or_404(Community, id=id)
    Membership.objects.filter(user=request.user, community=c).delete()
    messages.success(request, f'You are no longer a member of {c.name}.')
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


def community_json(request):
    q = request.GET.get('q', '').strip()
    communities = Community.objects.all()

    if request.user.is_authenticated:
        joined_ids = Membership.objects.filter(
            user=request.user
        ).values_list('community_id', flat=True)
        communities = communities.exclude(id__in=joined_ids)

    if q:
        communities = communities.filter(
            Q(name__icontains=q) |
            Q(short_description__icontains=q) |
            Q(full_description__icontains=q)
        )

    data = [
        {
            'id': c.id,
            'name': c.name,
            'short_description': c.short_description,
            'full_description': c.full_description,
            'created_at': c.created_at,
        }
        for c in communities
    ]

    return JsonResponse({
        'count': len(data),
        'results': data
    })


def community_detail_json(request, id):
    c = get_object_or_404(Community, id=id)

    memberships = Membership.objects.filter(
        community=c
    ).select_related('user')

    members_data = [
        {
            'id': m.user.id,
            'username': m.user.username,
            'role': m.role,
            'joined_at': m.joined_at
        }
        for m in memberships
    ]

    is_member = False
    user_role = None
    if request.user.is_authenticated:
        mem = Membership.objects.filter(user=request.user, community=c).first()
        if mem:
            is_member = True
            user_role = mem.role

    return JsonResponse({
        'id': c.id,
        'name': c.name,
        'short_description': c.short_description,
        'full_description': c.full_description,
        'created_at': c.created_at,
        'members_count': len(members_data),
        'members': members_data,
        'is_member': is_member,
        'user_role': user_role,
    })


@login_required
def join_community_json(request, id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    c = get_object_or_404(Community, id=id)

    membership, created = Membership.objects.get_or_create(
        community=c,
        user=request.user,
        defaults={'role': 'user'}
    )

    if created:
        return JsonResponse({'success': True, 'message': f'Joined {c.name}.'})
    else:
        return JsonResponse({'success': False, 'message': 'Already a member.'})


@login_required
def leave_community_json(request, id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    c = get_object_or_404(Community, id=id)

    deleted, _ = Membership.objects.filter(
        community=c,
        user=request.user
    ).delete()

    if deleted:
        return JsonResponse({'success': True, 'message': f'Left {c.name}.'})
    else:
        return JsonResponse({'success': False, 'message': 'You were not a member.'})

@login_required
def community_messages_json(request, id):
    community = get_object_or_404(Community, id=id)

    if not Membership.objects.filter(user=request.user, community=community).exists():
        return JsonResponse({'error': 'You are not a member.'}, status=403)

    messages_qs = Message.objects.filter(
        community=community
    ).select_related('sender').order_by('created_at')

    data = [
        {
            'id': m.id,
            'text': m.text,
            'sender': m.sender.username,
            'sender_id': m.sender.id,
            'created_at': m.created_at,
        }
        for m in messages_qs
    ]

    return JsonResponse({'count': len(data), 'messages': data})

@login_required
def send_message_json(request, id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    community = get_object_or_404(Community, id=id)

    if not Membership.objects.filter(user=request.user, community=community).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)

    body = json.loads(request.body)
    text = body.get('text', '').strip()

    if not text:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = Message.objects.create(
        community=community,
        sender=request.user,
        text=text
    )

    return JsonResponse({
        'id': msg.id,
        'text': msg.text,
        'sender': msg.sender.username,
        'sender_id': msg.sender.id,
        'created_at': msg.created_at,
    })

@login_required
def delete_message_json(request, id, msg_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    msg = get_object_or_404(Message, id=msg_id, sender=request.user)
    msg.delete()

    return JsonResponse({'success': True})


