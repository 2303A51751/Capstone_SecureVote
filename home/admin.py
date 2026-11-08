from django.contrib import admin
from .models import Voters, Vote, Block, VoteBackup, PoliticalParty, MiningInfo

admin.site.site_header = "Blockchain E-Voting Administration"
admin.site.site_title = "Blockchain Voting Portal"
admin.site.index_title = "Election & Blockchain Ledger Management"

@admin.register(Voters)
class VotersAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'dob', 'region', 'pincode', 'email', 'vote_done')
    list_filter = ('vote_done', 'region')
    search_fields = ('uuid', 'name', 'email', 'region')
    ordering = ('uuid',)
    actions = ['reset_vote_status']

    def reset_vote_status(self, request, queryset):
        queryset.update(vote_done=False)
    reset_vote_status.short_description = "Reset voting status (allow re-voting in demo)"

@admin.register(PoliticalParty)
class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ('party_id', 'party_name', 'candidate_name')
    search_fields = ('party_id', 'party_name', 'candidate_name')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'vote_party_id', 'timestamp', 'block_id_display')
    list_filter = ('vote_party_id', 'block_id')
    search_fields = ('uuid', 'vote_party_id', 'block_id')
    readonly_fields = ('timestamp',)

    def block_id_display(self, obj):
        return f"Block #{obj.block_id}" if obj.block_id else "Pending (Mempool)"
    block_id_display.short_description = "Block ID"

@admin.register(VoteBackup)
class VoteBackupAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'vote_party_id', 'timestamp', 'block_id')
    search_fields = ('uuid', 'vote_party_id')
    readonly_fields = ('timestamp',)

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'block_hash_short', 'merkle_hash_short', 'prev_hash_short', 'nonce', 'timestamp')
    readonly_fields = ('id', 'prev_hash', 'merkle_hash', 'this_hash', 'nonce', 'timestamp')
    ordering = ('-id',)

    def block_hash_short(self, obj):
        return f"{obj.this_hash[:16]}..." if obj.this_hash else "-"
    block_hash_short.short_description = "Block Hash"

    def merkle_hash_short(self, obj):
        return f"{obj.merkle_hash[:16]}..." if obj.merkle_hash else "-"
    merkle_hash_short.short_description = "Merkle Root"

    def prev_hash_short(self, obj):
        return f"{obj.prev_hash[:16]}..." if obj.prev_hash else "-"
    prev_hash_short.short_description = "Prev Hash"

@admin.register(MiningInfo)
class MiningInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_block_id', 'prev_hash_short')
    readonly_fields = ('prev_hash', 'last_block_id')

    def prev_hash_short(self, obj):
        return f"{obj.prev_hash[:20]}..." if obj.prev_hash else "-"
    prev_hash_short.short_description = "Previous Hash"
