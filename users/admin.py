from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Member, Coach

# Unregister the default User admin to replace it with a custom one
admin.site.unregister(User)

# Define an inline admin for the Member profile
class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'Member Profile'
    fk_name = 'user'
    fields = ('profile_photo', 'city', 'phone', 'description')

# Define an inline admin for the Coach profile
class CoachInline(admin.StackedInline):
    model = Coach
    can_delete = False
    verbose_name_plural = 'Coach Profile'
    fk_name = 'user'
    fields = ('profile_photo', 'sport', 'city', 'phone', 'hourly_fee', 'description')

# Define a new User admin that includes the profile inlines
class CustomUserAdmin(BaseUserAdmin):
    inlines = (MemberInline, CoachInline,)

    def get_inline_instances(self, request, obj=None):
        """
        Dynamically show the correct inline (Member or Coach) based on the user's profile.
        If the user has no profile (e.g., a superuser), no inline will be shown.
        """
        if not obj:
            return []
        
        inlines = []
        if hasattr(obj, 'member'):
            inlines.append(MemberInline(self.model, self.admin_site))
        if hasattr(obj, 'coach'):
            inlines.append(CoachInline(self.model, self.admin_site))
            
        return inlines

# Re-register the User model with our custom admin
admin.site.register(User, CustomUserAdmin)

# Register Member and Coach models separately for their own list views
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'city', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'city')
    
    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name()

@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'sport', 'city', 'hourly_fee')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'sport', 'city')
    list_filter = ('sport', 'city')

    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name()