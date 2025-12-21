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
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import HttpResponse


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

            # Redirect ke my_list agar langsung terlihat
            return redirect(reverse('community:my_list') + '?created=true')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = CommunityCreateForm()

    return render(request, 'community/create.html', {'form': form})

@csrf_exempt
@login_required
def community_create_json(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=400)

    try:
        body = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = body.get("name")
    short_description = body.get("short_description")
    full_description = body.get("full_description")
    profile_image_url = body.get("profile_image_url")

    # Create the community
    community = Community.objects.create(
        name=name,
        short_description=short_description,
        full_description=full_description,
        profile_image_url=profile_image_url,
        created_by=request.user
    )

    # Automatically add creator as admin
    Membership.objects.get_or_create(
        community=community,
        user=request.user,
        defaults={"role": "admin"}
    )

    data = {
        "id": community.id,
        "name": community.name,
        "short_description": community.short_description,
        "full_description": community.full_description,
        "profile_image_url": community.profile_image_url,
        "members_count": community.members_count(),
        "created_at": community.created_at.isoformat(),
        "created_by": community.created_by.username,
        "is_member": True,
        "user_role": "admin"
    }

    return JsonResponse(data, status=201)



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

@csrf_exempt
@login_required
def join_community_json(request, id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    community = get_object_or_404(Community, id=id)

    membership, created = Membership.objects.get_or_create(
        community=community,
        user=request.user,
        defaults={'role': 'user'}
    )

    community_data = {
        "id": community.id,
        "name": community.name,
        "short_description": community.short_description,
        "full_description": community.full_description,
        "profile_image_url": community.profile_image_url,
        "members_count": community.members_count(),
        "created_by": community.created_by.username,
        "is_member": True,
        "user_role": membership.role,
    }

    if created:
        return JsonResponse({
            'success': True,
            'message': f'Joined {community.name}.',
            'community': community_data
        })

    return JsonResponse({
        'success': False,
        'message': 'Already a member.',
        'community': community_data
    })



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

@login_required
def my_community_list_json(request):
    memberships = Membership.objects.filter(
        user=request.user
    ).select_related('community')

    data = [
        {
            "id": m.community.id,
            "name": m.community.name,
            "short_description": m.community.short_description,
            "full_description": m.community.full_description,
            "profile_image_url": m.community.profile_image_url,
            "members_count": m.community.members_count(),
            "created_at": m.community.created_at.isoformat(),
            "created_by": m.community.created_by.username,
        }
        for m in memberships
    ]

    # RETURN LIST — sesuai ekspektasi Flutter
    return JsonResponse(data, safe=False)

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



# LEAVE (hapus membership, balikin ke Community main)
@login_required
def leave_community(request, id):
    c = get_object_or_404(Community, id=id)
    Membership.objects.filter(user=request.user, community=c).delete()
    messages.success(request, f'You are no longer a member of {c.name}.')
    return redirect('community:home')

@csrf_exempt
@login_required
def leave_community_json(request, id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    community = get_object_or_404(Community, id=id)

    deleted, _ = Membership.objects.filter(
        community=community,
        user=request.user
    ).delete()

    community_data = {
        "id": community.id,
        "name": community.name,
        "short_description": community.short_description,
        "full_description": community.full_description,
        "profile_image_url": community.profile_image_url,
        "members_count": community.members_count(),
        "created_by": community.created_by.username,
        "is_member": False,
        "user_role": None
    }

    if deleted:
        return JsonResponse({
            'success': True,
            'message': f'Left {community.name}.',
            'community': community_data,
        })

    return JsonResponse({
        'success': False,
        'message': 'You were not a member.',
        'community': community_data
    })


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

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
@login_required
def my_community_group_json(request, id):
    community = get_object_or_404(Community, id=id)

    # --- Check membership ---
    membership = Membership.objects.filter(
        user=request.user,
        community=community
    ).first()

    if not membership:
        return JsonResponse({
            "success": False,
            "error": "You must join this community first."
        }, status=403)

    # --- POST: Send message ---
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON"
            }, status=400)

        text = data.get("text", "").strip()
        if not text:
            return JsonResponse({
                "success": False,
                "error": "Message cannot be empty."
            }, status=400)

        msg = Message.objects.create(
            community=community,
            sender=request.user,
            text=text
        )

        return JsonResponse({
            "success": True,
            "message": "Message sent.",
            "data": {
                "id": msg.id,
                "text": msg.text,
                "sender": msg.sender.username,
                "sender_id": msg.sender.id,
                "created_at": msg.created_at,
            }
        }, status=201)

    # --- GET: Return full group details ---
    messages_qs = Message.objects.filter(
        community=community
    ).select_related("sender").order_by("created_at")

    messages_data = [
        {
            "id": m.id,
            "text": m.text,
            "sender": m.sender.username,
            "sender_id": m.sender.id,
            "created_at": m.created_at,
        }
        for m in messages_qs
    ]

    return JsonResponse({
        "success": True,
        "community": {
            "id": community.id,
            "name": community.name,
            "short_description": community.short_description,
            "full_description": community.full_description,
            "members_count": community.members_count(),
        },
        "messages": messages_data,
        "is_member": True,
        "user_role": membership.role,
    })



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

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@login_required
def edit_message_json(request, id, msg_id):
    # pastikan pesan milik user
    message = get_object_or_404(Message, id=msg_id, sender=request.user)

    if request.method not in ["PUT", "POST"]:
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_text = data.get("text", "").strip()

    if not new_text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    message.text = new_text
    message.save()

    return JsonResponse({
        'success': True,
        'message': 'Message updated successfully',
        'data': {
            'id': message.id,
            'text': message.text,
            'sender': message.sender.username,
            'created_at': message.created_at,
        }
    })


@login_required
def delete_message(request, id, msg_id):
    """Hapus pesan via AJAX"""
    if request.method == 'DELETE':
        message = get_object_or_404(Message, id=msg_id, sender=request.user)
        message.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)



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



def communities_json(request):
    # Ambil semua komunitas
    communities = Community.objects.all()

    # Jika user login, hilangkan komunitas yang sudah dijoin
    if request.user.is_authenticated:
        joined_ids = Membership.objects.filter(
            user=request.user
        ).values_list("community_id", flat=True)
        communities = communities.exclude(id__in=joined_ids)

    # Optimasi query
    communities = communities.select_related("created_by")

    # Format JSON sesuai kebutuhan Flutter
    data = [
        {
            "id": c.id,
            "name": c.name,
            "short_description": c.short_description,
            "full_description": c.full_description,
            "profile_image_url": c.profile_image_url,
            "members_count": c.members_count(),
            "created_at": c.created_at.isoformat(),
            "created_by": c.created_by.username,
        }
        for c in communities
    ]

    return JsonResponse(data, safe=False)



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



@csrf_exempt
@login_required
def delete_message_json(request, id, msg_id):
    if request.method != 'POST':   
        return JsonResponse({'error': 'Invalid method'}, status=405)

    msg = get_object_or_404(Message, id=msg_id, sender=request.user)
    msg.delete()

    return JsonResponse({'success': True})

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)



