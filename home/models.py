from django.db import models

class Voters(models.Model):
    uuid = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    dob = models.DateField()
    pincode = models.CharField(max_length=6)
    region = models.CharField(max_length=100)
    profile_pic = models.CharField(max_length=500, blank=True)
    email = models.CharField(max_length=100, blank=True)
    vote_done = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Voter"
        verbose_name_plural = "Voters"

    def __str__(self):
        status = "Voted" if self.vote_done else "Pending"
        return f"{self.name} (UID: {self.uuid}) [{status}]"

class PoliticalParty(models.Model):
    party_id = models.CharField(max_length=10, primary_key=True)
    party_name = models.CharField(max_length=100)
    party_logo = models.CharField(max_length=500)
    candidate_name = models.CharField(max_length=100, blank=True)
    candidate_profile_pic = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Political Party"
        verbose_name_plural = "Political Parties"

    def __str__(self):
        return f"{self.party_name} ({self.party_id})"

class Vote(models.Model):
    uuid = models.CharField(max_length=20, primary_key=True)
    vote_party_id = models.CharField(max_length=10)
    timestamp = models.DateTimeField()
    block_id = models.CharField(null=True, max_length=10, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Vote"
        verbose_name_plural = "Votes"

    def __str__(self):
        block_str = f"Block #{self.block_id}" if self.block_id else "Unmined (Mempool)"
        return f"Vote {self.uuid} -> {self.vote_party_id} [{block_str}]"

class VoteBackup(models.Model):
    uuid = models.CharField(max_length=20, primary_key=True)
    vote_party_id = models.CharField(max_length=10)
    timestamp = models.DateTimeField()
    block_id = models.CharField(null=True, max_length=10, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Vote Backup (Consensus Ledger)"
        verbose_name_plural = "Vote Backups (Consensus Ledgers)"

    def __str__(self):
        return f"Backup {self.uuid} -> {self.vote_party_id}"

class Block(models.Model):
    prev_hash = models.CharField(max_length=100, blank=True)
    merkle_hash = models.CharField(max_length=100, blank=True)
    this_hash = models.CharField(max_length=100, blank=True)
    nonce = models.IntegerField(null=True)
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ['id']
        verbose_name = "Blockchain Block"
        verbose_name_plural = "Blockchain Blocks"

    def __str__(self):
        return f"Block #{self.id} [Nonce: {self.nonce}] - Hash: {self.this_hash[:12]}..."

class MiningInfo(models.Model):
    prev_hash = models.CharField(max_length=100, blank=True)
    last_block_id = models.CharField(null=True, max_length=10, blank=True)

    class Meta:
        verbose_name = "Mining Info"
        verbose_name_plural = "Mining Info"

    def __str__(self):
        return f"Mining Status (Last Block #{self.last_block_id})"
