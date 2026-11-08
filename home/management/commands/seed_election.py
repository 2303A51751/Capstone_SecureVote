from django.core.management.base import BaseCommand
from home.views import dummy_data_input
from home.models import Voters, PoliticalParty, Vote, Block

class Command(BaseCommand):
    help = 'Seeds realistic election data (parties, citizens, initial votes) for testing and viva presentation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--votes',
            action='store_true',
            default=True,
            help='Cast initial sample votes into the mempool (leaves 4 citizens unvoted)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Initializing and seeding election database...'))
        dummy_data_input({
            'createPoliticianParties': True,
            'createRandomVoters': True,
            'castRandomVote': options['votes']
        })
        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded database:\n'
            f'- Political Parties: {PoliticalParty.objects.count()}\n'
            f'- Registered Citizens: {Voters.objects.count()} (4 ready to vote, 6 initial votes cast)\n'
            f'- Votes in Mempool: {Vote.objects.filter(block_id=None).count()}\n'
            f'- Sealed Blocks: {Block.objects.count()}'
        ))

