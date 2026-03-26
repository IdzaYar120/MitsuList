from django.contrib import admin
from .models import ChatThread, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    ordering = ('timestamp',)

@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'updated_at')
    inlines = [ChatMessageInline]
    search_fields = ('user1__username', 'user2__username')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'timestamp', 'text_snippet')
    list_filter = ('sender',)
    
    def text_snippet(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
