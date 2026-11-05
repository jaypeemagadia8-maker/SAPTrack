from django.contrib import admin

from .models import Area, AreaAssignment, Room, RoomAssignment


admin.site.register(Room)
admin.site.register(Area)
admin.site.register(RoomAssignment)
admin.site.register(AreaAssignment)
