"""
Management command: python manage.py seed_data
Creates realistic test data for PharmaPOS.
Safe to run multiple times -- skips already-existing records.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seed the database with realistic pharmacy test data'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()
        self.seed_settings()
        self.seed_users()
        self.seed_counters()
        self.seed_partners()
        self.seed_categories()
        self.seed_suppliers()
        self.seed_drugs()
        self.seed_customers()
        self.seed_purchases()
        self.seed_sales()
        self.stdout.write(self.style.SUCCESS('\nSeed data complete!'))

    def clear_data(self):
        from apps.sales.models import ReturnItem, Return, SaleItem, Sale, DayClosing, Customer
        from apps.inventory.models import StockAdjustment, PurchaseItem, Purchase, Drug, Supplier, Category
        from apps.accounts.models import Partner, Counter, User

        self.stdout.write('Clearing existing data...')
        ReturnItem.objects.all().delete()
        Return.objects.all().delete()
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        DayClosing.objects.all().delete()
        Customer.objects.all().delete()
        StockAdjustment.objects.all().delete()
        PurchaseItem.objects.all().delete()
        Purchase.objects.all().delete()
        Drug.objects.all().delete()
        Supplier.objects.all().delete()
        Category.objects.all().delete()
        Partner.objects.all().delete()
        Counter.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('  done.\n')

    def seed_settings(self):
        from apps.settings_app.models import PharmacySettings
        s = PharmacySettings.get_settings()
        s.pharmacy_name       = 'Al-Shifa Pharmacy'
        s.tagline             = 'Your Health, Our Priority'
        s.phone               = '0300-1234567'
        s.email               = 'info@alshifa-pharmacy.pk'
        s.address             = 'Shop #12, Main Bazaar, Lahore, Pakistan'
        s.currency            = 'Rs'
        s.tax_rate            = 0
        s.return_days         = 15
        s.low_stock_threshold = 10
        s.receipt_footer      = 'Thank you for choosing Al-Shifa Pharmacy. Get well soon!'
        s.save()
        self.stdout.write('  [OK] Settings')

    def seed_users(self):
        from apps.accounts.models import User
        users = [
            ('ali_pharmacist', 'Ali Hassan',      'pharmacist', 'Test@1234'),
            ('sara_cashier',   'Sara Ahmed',       'cashier',    'Test@1234'),
            ('usman_cashier',  'Usman Tariq',      'cashier',    'Test@1234'),
            ('maryam_partner', 'Maryam Siddiqui',  'partner',    'Test@1234'),
            ('bilal_partner',  'Bilal Khan',        'partner',    'Test@1234'),
        ]
        for username, full_name, role, password in users:
            if not User.objects.filter(username=username).exists():
                first, *last = full_name.split()
                User.objects.create_user(
                    username=username, password=password,
                    first_name=first, last_name=' '.join(last),
                    email=f'{username}@alshifa.pk',
                    role=role,
                )
        self.stdout.write('  [OK] Users (5 created -- password: Test@1234)')

    def seed_counters(self):
        from apps.accounts.models import Counter, User
        data = [
            ('Counter 1', 'sara_cashier'),
            ('Counter 2', 'usman_cashier'),
        ]
        for name, cashier_username in data:
            if not Counter.objects.filter(name=name).exists():
                cashier = User.objects.filter(username=cashier_username).first()
                Counter.objects.create(name=name, cashier=cashier, is_active=True)
        self.stdout.write('  [OK] Counters (2)')

    def seed_partners(self):
        from apps.accounts.models import Partner, User
        data = [
            ('maryam_partner', 60.00, 'Senior partner -- founding member'),
            ('bilal_partner',  40.00, 'Junior partner -- joined 2023'),
        ]
        for username, pct, notes in data:
            user = User.objects.filter(username=username).first()
            if user and not Partner.objects.filter(user=user).exists():
                Partner.objects.create(user=user, ownership_percent=pct, notes=notes)
        self.stdout.write('  [OK] Partners (2 -- 60% / 40%)')

    def seed_categories(self):
        from apps.inventory.models import Category
        cats = [
            ('Antibiotics',    'Bacterial infection treatments'),
            ('Analgesics',     'Pain relief medications'),
            ('Antacids',       'Stomach acid relief'),
            ('Antihistamines', 'Allergy medications'),
            ('Vitamins',       'Vitamins and supplements'),
            ('Cardiovascular', 'Heart and blood pressure medications'),
            ('Diabetes',       'Diabetes management drugs'),
            ('Dermatology',    'Skin care medications'),
            ('Cough & Cold',   'Cold, cough and flu remedies'),
            ('Eye & Ear',      'Ophthalmic and otic preparations'),
            ('Neurological',   'Nerve and brain related medications'),
            ('Gastro',         'Gastrointestinal medications'),
            ('Respiratory',    'Asthma and lung medications'),
            ('Hormones',       'Hormonal and thyroid medications'),
            ('Injections',     'Injectable medications and vaccines'),
        ]
        for name, desc in cats:
            Category.objects.get_or_create(name=name, defaults={'description': desc})
        self.stdout.write('  [OK] Categories (15)')

    def seed_suppliers(self):
        from apps.inventory.models import Supplier
        suppliers = [
            ('MedPharma Ltd',         '042-35761234', 'orders@medpharma.pk',   'Gulberg, Lahore',   'Mr. Khurram'),
            ('Al-Habib Distributors', '021-34567890', 'sales@alhabib.pk',      'Saddar, Karachi',   'Ms. Farah'),
            ('Zaka Medical Supplies', '051-2345678',  'info@zakamedical.pk',   'G-9, Islamabad',    'Mr. Zaka'),
            ('Rex Pharma',            '042-36001122', 'sales@rexpharma.pk',    'Johar Town, Lahore','Mr. Usman'),
            ('Sami Pharmaceuticals',  '021-32400100', 'info@samipharma.pk',    'SITE, Karachi',     'Ms. Hira'),
        ]
        for name, phone, email, address, contact in suppliers:
            Supplier.objects.get_or_create(
                name=name,
                defaults=dict(phone=phone, email=email, address=address,
                              contact_person=contact, is_active=True)
            )
        self.stdout.write('  [OK] Suppliers (5)')

    def seed_drugs(self):
        from apps.inventory.models import Drug, Category, Supplier
        today = date.today()

        def cat(name): return Category.objects.get(name=name)
        def sup(k):    return Supplier.objects.get(name__icontains=k)

        # brand, strength, generic, category, supplier_key,
        # barcode, sale_price, cost_price, qty, reorder, expiry_days, pcs_per_pack, pack_price
        drugs = [
            # ── Antibiotics ───────────────────────────────────────────────────
            ('Amoxil',        '250mg',       'Amoxicillin',           'Antibiotics',    'MedPharma', 'AMX250',    95,   50,  150, 20, 540, 14,  1250),
            ('Amoxil',        '500mg',       'Amoxicillin',           'Antibiotics',    'MedPharma', 'AMX500',   180,   95,  200, 20, 540, 14,  2400),
            ('Augmentin',     '375mg',       'Amoxiclav',             'Antibiotics',    'Al-Habib',  'AUG375',   280,  150,  100, 10, 480, 14,  3700),
            ('Augmentin',     '625mg',       'Amoxiclav',             'Antibiotics',    'MedPharma', 'AUG625',   450,  250,  150, 15, 480, 14,  6000),
            ('Flagyl',        '200mg',       'Metronidazole',         'Antibiotics',    'Al-Habib',  'FLG200',    55,   25,  200, 20, 600, 20,  1050),
            ('Flagyl',        '400mg',       'Metronidazole',         'Antibiotics',    'Al-Habib',  'FLG400',    85,   40,  300, 30, 600, 20,  1600),
            ('Ciprofloxacin', '250mg',       'Ciprofloxacin',         'Antibiotics',    'Rex',       'CIP250',   120,   60,  180, 20, 480, 10,  1150),
            ('Ciprofloxacin', '500mg',       'Ciprofloxacin',         'Antibiotics',    'Rex',       'CIP500',   220,  110,  160, 15, 480, 10,  2100),
            ('Erythrocin',    '250mg',       'Erythromycin',          'Antibiotics',    'Sami',      'ERY250',   150,   75,  120, 15, 400, 16,  2250),
            ('Erythrocin',    '500mg',       'Erythromycin',          'Antibiotics',    'Sami',      'ERY500',   260,  130,  100, 10, 400, 16,  3900),
            ('Doxycycline',   '100mg',       'Doxycycline',           'Antibiotics',    'Zaka',      'DOX100',   110,   55,  200, 20, 540, 10,  1050),
            ('Klacid',        '250mg',       'Clarithromycin',        'Antibiotics',    'MedPharma', 'KLC250',   280,  140,  120, 12, 400, 14,  3700),
            ('Klacid',        '500mg',       'Clarithromycin',        'Antibiotics',    'MedPharma', 'KLC500',   480,  240,   80, 10, 400, 14,  6400),
            ('Septran',       'DS',          'Co-trimoxazole',        'Antibiotics',    'Al-Habib',  'SEP001',    65,   30,  300, 30, 600, 20,  1250),

            # ── Analgesics ────────────────────────────────────────────────────
            ('Panadol',       '500mg',       'Paracetamol',           'Analgesics',     'Al-Habib',  'PAN500',    20,   10,  500, 50, 730, 30,   580),
            ('Panadol',       'Extra',       'Paracetamol+Caffeine',  'Analgesics',     'Al-Habib',  'PANEXT',    35,   18,  400, 50, 730, 30,  1000),
            ('Panadol',       'Extend',      'Paracetamol SR',        'Analgesics',     'Al-Habib',  'PANXR',     55,   28,  300, 30, 730, 20,  1050),
            ('Brufen',        '200mg',       'Ibuprofen',             'Analgesics',     'MedPharma', 'BRF200',    45,   22,  200, 20, 365, 20,   850),
            ('Brufen',        '400mg',       'Ibuprofen',             'Analgesics',     'MedPharma', 'BRF400',    75,   38,  250, 25, 365, 20,  1400),
            ('Brufen',        '600mg',       'Ibuprofen',             'Analgesics',     'MedPharma', 'BRF600',   110,   55,  150, 15, 365, 20,  2100),
            ('Voltaren',      '25mg',        'Diclofenac',            'Analgesics',     'Zaka',      'VLT025',    80,   40,  200, 20, 400, 20,  1500),
            ('Voltaren',      '50mg',        'Diclofenac',            'Analgesics',     'Zaka',      'VLT050',   120,   60,  180, 20, 400, 20,  2200),
            ('Meftal',        '250mg',       'Mefenamic Acid',        'Analgesics',     'Rex',       'MFT250',    75,   38,  200, 20, 400, 20,  1400),
            ('Meftal',        '500mg',       'Mefenamic Acid',        'Analgesics',     'Rex',       'MFT500',   110,   55,  150, 15, 400, 20,  2100),
            ('Aspirin',       '75mg',        'Acetylsalicylic Acid',  'Cardiovascular', 'Zaka',      'ASP075',    55,   28,  300, 30, 730, 30,  1550),
            ('Aspirin',       '300mg',       'Acetylsalicylic Acid',  'Analgesics',     'Zaka',      'ASP300',    35,   18,  200, 20, 730, 20,   650),
            ('Tramadol',      '50mg',        'Tramadol HCl',          'Analgesics',     'Sami',      'TRM050',   120,   60,  100, 10, 365, 10,  1150),

            # ── Antacids / Gastro ─────────────────────────────────────────────
            ('Gaviscon',      'Liquid',      'Alginate Antacid',      'Antacids',       'Al-Habib',  'GAV001',   280,  140,  100, 10, 500,  1,   280),
            ('Gaviscon',      'Tablets',     'Alginate Antacid',      'Antacids',       'Al-Habib',  'GAV002',   180,   90,  150, 15, 500, 32,  5600),
            ('Histac',        '150mg',       'Ranitidine',            'Antacids',       'MedPharma', 'HST150',    90,   45,  200, 20, 360, 20,  1700),
            ('Nexium',        '20mg',        'Esomeprazole',          'Gastro',         'Sami',      'NEX020',   320,  160,  150, 15, 400, 14,  4300),
            ('Nexium',        '40mg',        'Esomeprazole',          'Gastro',         'Sami',      'NEX040',   480,  240,  100, 10, 400, 14,  6500),
            ('Omeprazole',    '20mg',        'Omeprazole',            'Gastro',         'Rex',       'OMP020',   120,   60,  300, 30, 540, 14,  1600),
            ('Losec',         '20mg',        'Omeprazole',            'Gastro',         'MedPharma', 'LSC020',   280,  140,  150, 15, 400, 14,  3700),
            ('Motilium',      '10mg',        'Domperidone',           'Gastro',         'Al-Habib',  'MOT010',   110,   55,  200, 20, 400, 30,  3200),
            ('Flagyl',        '500mg Susp',  'Metronidazole Susp',    'Gastro',         'Zaka',      'FLG500S',  140,   70,  120, 12, 360,  1,   140),
            ('Immodium',      '2mg',         'Loperamide',            'Gastro',         'Rex',       'IMD002',    85,   42,  200, 20, 500, 12,   980),

            # ── Antihistamines ────────────────────────────────────────────────
            ('Zyrtec',        '5mg',         'Cetirizine',            'Antihistamines', 'Al-Habib',  'ZYR005',    75,   38,  250, 25, 450, 14,   990),
            ('Zyrtec',        '10mg',        'Cetirizine',            'Antihistamines', 'Al-Habib',  'ZYR010',   110,   55,  220, 20, 450, 14,  1450),
            ('Allegra',       '120mg',       'Fexofenadine',          'Antihistamines', 'Zaka',      'ALG120',   195,   95,  150, 15, 400, 10,  1850),
            ('Allegra',       '180mg',       'Fexofenadine',          'Antihistamines', 'Zaka',      'ALG180',   260,  130,  100, 10, 400, 10,  2450),
            ('Phenergan',     '10mg',        'Promethazine',          'Antihistamines', 'Sami',      'PHN010',    90,   45,  200, 20, 400, 20,  1700),
            ('Clarinase',     '5mg',         'Loratadine+Pseudo',     'Antihistamines', 'MedPharma', 'CLR005',   320,  160,  100, 10, 400, 10,  3050),
            ('Loratadine',    '10mg',        'Loratadine',            'Antihistamines', 'Rex',       'LOR010',    85,   42,  250, 25, 500, 14,  1150),

            # ── Vitamins & Supplements ────────────────────────────────────────
            ('Centrum',       'Silver',      'Multivitamin',          'Vitamins',       'MedPharma', 'CTR001',   850,  450,   80, 10, 720, 30, 24000),
            ('Centrum',       'Kids',        'Multivitamin Chewable', 'Vitamins',       'MedPharma', 'CTR002',   650,  340,  100, 12, 720, 30, 18500),
            ('Vitamin C',     '500mg',       'Ascorbic Acid',         'Vitamins',       'Al-Habib',  'VTC500',    45,   22,  400, 40, 600, 30,  1250),
            ('Vitamin C',     '1000mg',      'Ascorbic Acid',         'Vitamins',       'Al-Habib',  'VTC1000',   80,   40,  300, 30, 600, 30,  2300),
            ('Vitamin D3',    '1000IU',      'Cholecalciferol',       'Vitamins',       'Zaka',      'VTD1000',  120,   60,  250, 25, 720, 30,  3400),
            ('Vitamin D3',    '5000IU',      'Cholecalciferol',       'Vitamins',       'Zaka',      'VTD5000',  380,  190,  150, 15, 720, 30, 11000),
            ('Omega-3',       '1000mg',      'Fish Oil',              'Vitamins',       'Sami',      'OMG001',   650,  320,   60,  8, 540, 30, 18500),
            ('Zinc Sulphate', '20mg',        'Zinc Sulphate',         'Vitamins',       'Rex',       'ZNC020',    65,   32,  300, 30, 600, 30,  1850),
            ('Calcium',       '500mg',       'Calcium Carbonate',     'Vitamins',       'Al-Habib',  'CAL500',    85,   42,  300, 30, 720, 30,  2450),
            ('Calcium',       '1000mg',      'Calcium Carbonate',     'Vitamins',       'Al-Habib',  'CAL1000',  150,   75,  200, 20, 720, 30,  4250),
            ('Folic Acid',    '5mg',         'Folic Acid',            'Vitamins',       'MedPharma', 'FOL005',    30,   15,  400, 40, 720, 30,   850),
            ('Iron',          '150mg',       'Ferrous Sulphate',      'Vitamins',       'Rex',       'IRN150',    55,   28,  300, 30, 600, 30,  1550),

            # ── Cardiovascular ────────────────────────────────────────────────
            ('Norvasc',       '5mg',         'Amlodipine',            'Cardiovascular', 'MedPharma', 'NRV005',   280,  140,  180, 18, 365, 14,  3700),
            ('Norvasc',       '10mg',        'Amlodipine',            'Cardiovascular', 'MedPharma', 'NRV010',   420,  210,  120, 15, 365, 14,  5600),
            ('Concor',        '2.5mg',       'Bisoprolol',            'Cardiovascular', 'Al-Habib',  'CNC025',   220,  110,  150, 15, 400, 14,  2900),
            ('Concor',        '5mg',         'Bisoprolol',            'Cardiovascular', 'Al-Habib',  'CNC005',   320,  160,  150, 15, 400, 14,  4200),
            ('Concor',        '10mg',        'Bisoprolol',            'Cardiovascular', 'Al-Habib',  'CNC010',   480,  240,  100, 10, 400, 14,  6400),
            ('Cozaar',        '50mg',        'Losartan',              'Cardiovascular', 'Sami',      'COZ050',   420,  210,  120, 12, 365, 14,  5600),
            ('Cozaar',        '100mg',       'Losartan',              'Cardiovascular', 'Sami',      'COZ100',   680,  340,   80, 10, 365, 14,  9100),
            ('Atenolol',      '50mg',        'Atenolol',              'Cardiovascular', 'Rex',       'ATN050',   120,   60,  200, 20, 400, 20,  2300),
            ('Atenolol',      '100mg',       'Atenolol',              'Cardiovascular', 'Rex',       'ATN100',   180,   90,  150, 15, 400, 20,  3400),
            ('Simvastatin',   '20mg',        'Simvastatin',           'Cardiovascular', 'Zaka',      'SIM020',   220,  110,  180, 18, 400, 14,  2900),
            ('Simvastatin',   '40mg',        'Simvastatin',           'Cardiovascular', 'Zaka',      'SIM040',   320,  160,  120, 12, 400, 14,  4250),
            ('Eltroxin',      '50mcg',       'Levothyroxine',         'Hormones',       'MedPharma', 'ELT050',   420,  210,  100, 10, 400, 30, 11900),
            ('Eltroxin',      '100mcg',      'Levothyroxine',         'Hormones',       'MedPharma', 'ELT100',   580,  290,   80,  8, 400, 30, 16500),
            ('Digoxin',       '0.25mg',      'Digoxin',               'Cardiovascular', 'Sami',      'DGX025',   180,   90,  150, 15, 365, 20,  3400),

            # ── Diabetes ──────────────────────────────────────────────────────
            ('Glucophage',    '500mg',       'Metformin',             'Diabetes',       'Zaka',      'GLC500',   180,   88,  200, 20, 360, 30,  5200),
            ('Glucophage',    '850mg',       'Metformin',             'Diabetes',       'Zaka',      'GLC850',   240,  120,  160, 15, 360, 30,  6900),
            ('Glucophage',    '1000mg',      'Metformin',             'Diabetes',       'Zaka',      'GLC1000',  320,  160,  120, 15, 360, 30,  9200),
            ('Amaryl',        '1mg',         'Glimepiride',           'Diabetes',       'Sami',      'AMR001',   180,   90,  150, 15, 360, 30,  5200),
            ('Amaryl',        '2mg',         'Glimepiride',           'Diabetes',       'Sami',      'AMR002',   280,  140,  120, 12, 360, 30,  8000),
            ('Amaryl',        '4mg',         'Glimepiride',           'Diabetes',       'Sami',      'AMR004',   420,  210,  100, 10, 360, 30, 12000),
            ('Lantus',        'SoloStar',    'Insulin Glargine',      'Diabetes',       'MedPharma', 'LNT001',  2800, 1500,   40,  5, 180,  1,  2800),
            ('Novorapid',     'FlexPen',     'Insulin Aspart',        'Diabetes',       'MedPharma', 'NVR001',  2600, 1400,   30,  5, 180,  1,  2600),
            ('Januvia',       '50mg',        'Sitagliptin',           'Diabetes',       'Rex',       'JAN050',   980,  490,   60,  6, 360, 28, 25900),
            ('Jardiance',     '10mg',        'Empagliflozin',         'Diabetes',       'Rex',       'JRD010',  1800,  900,   40,  5, 360, 28, 47600),

            # ── Dermatology ───────────────────────────────────────────────────
            ('Betnovate',     'Cream',       'Betamethasone',         'Dermatology',    'Al-Habib',  'BTV001',   145,   72,  120, 12, 540,  1,   145),
            ('Betnovate',     'Scalp',       'Betamethasone Solution', 'Dermatology',   'Al-Habib',  'BTV002',   220,  110,   80,  8, 540,  1,   220),
            ('Fusiderm',      'Cream',       'Fusidic Acid',          'Dermatology',    'Zaka',      'FSD001',   320,  160,   90, 10, 480,  1,   320),
            ('Canesten',      'Cream',       'Clotrimazole',          'Dermatology',    'MedPharma', 'CNS001',   280,  140,  100, 10, 540,  1,   280),
            ('Canesten',      'Pessary',     'Clotrimazole 500mg',    'Dermatology',    'MedPharma', 'CNS002',   420,  210,   60,  8, 540,  1,   420),
            ('Nizoral',       'Shampoo',     'Ketoconazole',          'Dermatology',    'Rex',       'NZR001',   480,  240,   70,  8, 720,  1,   480),
            ('Nizoral',       'Cream',       'Ketoconazole',          'Dermatology',    'Rex',       'NZR002',   320,  160,   80,  8, 540,  1,   320),
            ('Dermovate',     'Cream',       'Clobetasol',            'Dermatology',    'Sami',      'DRV001',   280,  140,   90,  9, 540,  1,   280),
            ('Calamine',      'Lotion',      'Calamine',              'Dermatology',    'Al-Habib',  'CLM001',    85,   42,  150, 15, 720,  1,    85),

            # ── Cough & Cold ──────────────────────────────────────────────────
            ('Benylin',       'Cough Syrup', 'Dextromethorphan',      'Cough & Cold',   'MedPharma', 'BNY001',   245,  120,  160, 15, 360,  1,   245),
            ('Benylin',       'Dry Cough',   'Dextromethorphan DM',   'Cough & Cold',   'MedPharma', 'BNY002',   280,  140,  120, 12, 360,  1,   280),
            ('Sinopharm',     'Cold Tab',    'Chlorphenamine',        'Cough & Cold',   'Al-Habib',  'SNP001',    95,   48,  200, 20, 400, 10,   900),
            ('Otrivin',       'Adult',       'Xylometazoline 0.1%',   'Cough & Cold',   'Zaka',      'OTV001',   175,   85,  140, 14, 420,  1,   175),
            ('Otrivin',       'Baby',        'Xylometazoline 0.05%',  'Cough & Cold',   'Zaka',      'OTV002',   175,   85,  100, 12, 420,  1,   175),
            ('Vicks',         'VapoRub',     'Camphor+Menthol',       'Cough & Cold',   'Rex',       'VCK001',   180,   90,  120, 12, 720,  1,   180),
            ('Vicks',         'Inhaler',     'Menthol+Camphor',       'Cough & Cold',   'Rex',       'VCK002',    95,   48,  150, 15, 540,  1,    95),
            ('Prospan',       'Syrup',       'Ivy Leaf Extract',      'Cough & Cold',   'Sami',      'PRS001',   380,  190,   80,  8, 360,  1,   380),
            ('Mucosolvan',    'Syrup',       'Ambroxol',              'Cough & Cold',   'MedPharma', 'MCS001',   245,  120,  100, 10, 360,  1,   245),
            ('Mucosolvan',    'Tablets',     'Ambroxol 30mg',         'Cough & Cold',   'MedPharma', 'MCS002',   180,   90,  150, 15, 400, 20,  3400),

            # ── Eye & Ear ─────────────────────────────────────────────────────
            ('Tobrex',        'Eye Drops',   'Tobramycin',            'Eye & Ear',      'MedPharma', 'TBX001',   380,  190,   80,  8, 300,  1,   380),
            ('Otosporin',     'Ear Drops',   'Polymyxin',             'Eye & Ear',      'Al-Habib',  'OTS001',   420,  210,   70,  7, 350,  1,   420),
            ('Systane',       'Eye Drops',   'Polyethylene Glycol',   'Eye & Ear',      'Zaka',      'SYS001',   480,  240,   60,  6, 540,  1,   480),
            ('Voltaren',      'Eye Drops',   'Diclofenac 0.1%',       'Eye & Ear',      'Sami',      'VLTE01',   320,  160,   70,  7, 360,  1,   320),
            ('Chlorsig',      'Eye Drops',   'Chloramphenicol',       'Eye & Ear',      'Rex',       'CLS001',   220,  110,   90,  9, 300,  1,   220),
            ('Waxsol',        'Ear Drops',   'Docusate Sodium',       'Eye & Ear',      'MedPharma', 'WXS001',   180,   90,  100, 10, 540,  1,   180),
            ('Similasan',     'Eye Drops',   'Homeopathic',           'Eye & Ear',      'Zaka',      'SML001',   350,  175,   60,  6, 540,  1,   350),

            # ── Respiratory ───────────────────────────────────────────────────
            ('Ventolin',      'Inhaler',     'Salbutamol 100mcg',     'Respiratory',    'Sami',      'VNT001',   380,  190,   80,  8, 365,  1,   380),
            ('Ventolin',      'Nebules',     'Salbutamol 2.5mg',      'Respiratory',    'Sami',      'VNT002',    85,   42,  200, 20, 365, 20,  1600),
            ('Seretide',      '25/50',       'Salmeterol+Fluticasone','Respiratory',    'MedPharma', 'SRT001',  2200, 1100,   40,  5, 365,  1,  2200),
            ('Seretide',      '25/125',      'Salmeterol+Fluticasone','Respiratory',    'MedPharma', 'SRT002',  3200, 1600,   30,  4, 365,  1,  3200),
            ('Singulair',     '5mg',         'Montelukast',           'Respiratory',    'Al-Habib',  'SNG005',   480,  240,  100, 10, 400, 28, 12900),
            ('Singulair',     '10mg',        'Montelukast',           'Respiratory',    'Al-Habib',  'SNG010',   680,  340,   80,  8, 400, 28, 18200),
            ('Atrovent',      'Inhaler',     'Ipratropium',           'Respiratory',    'Rex',       'ATR001',   650,  325,   50,  6, 365,  1,   650),
            ('Theo-Asthalin', '100mg',       'Theophylline',          'Respiratory',    'Zaka',      'THA100',   120,   60,  200, 20, 400, 20,  2300),

            # ── Neurological ──────────────────────────────────────────────────
            ('Depakine',      '200mg',       'Sodium Valproate',      'Neurological',   'Sami',      'DPK200',   280,  140,  100, 10, 400, 30,  8000),
            ('Depakine',      '500mg',       'Sodium Valproate',      'Neurological',   'Sami',      'DPK500',   420,  210,   80,  8, 400, 30, 12000),
            ('Tegretol',      '200mg',       'Carbamazepine',         'Neurological',   'MedPharma', 'TGR200',   280,  140,  100, 10, 400, 30,  8000),
            ('Rivotril',      '0.5mg',       'Clonazepam',            'Neurological',   'Rex',       'RVT005',   180,   90,  120, 12, 365, 30,  5200),
            ('Rivotril',      '2mg',         'Clonazepam',            'Neurological',   'Rex',       'RVT002',   280,  140,  100, 10, 365, 30,  8000),
            ('Lexotanil',     '1.5mg',       'Bromazepam',            'Neurological',   'Al-Habib',  'LEX015',   180,   90,  120, 12, 365, 30,  5200),
            ('Inderal',       '40mg',        'Propranolol',           'Neurological',   'Zaka',      'IND040',   120,   60,  200, 20, 400, 30,  3400),
            ('Stugeron',      '25mg',        'Cinnarizine',           'Neurological',   'MedPharma', 'STG025',    65,   32,  250, 25, 400, 20,  1250),
            ('Stugeron',      'Forte',       'Cinnarizine 75mg',      'Neurological',   'MedPharma', 'STGF01',    95,   48,  200, 20, 400, 20,  1800),

            # ── Hormones ──────────────────────────────────────────────────────
            ('Proluton',      '250mg',       'Hydroxyprogesterone',   'Hormones',       'Sami',      'PRO001',   380,  190,   50,  5, 300,  1,   380),
            ('Duphaston',     '10mg',        'Dydrogesterone',        'Hormones',       'MedPharma', 'DUP010',   680,  340,   60,  6, 365, 20, 13000),
            ('Clomid',        '50mg',        'Clomifene',             'Hormones',       'Rex',       'CLM050',   420,  210,   40,  5, 365,  5,  2000),
            ('Ovestin',       'Cream',       'Estriol',               'Hormones',       'Sami',      'OVT001',   680,  340,   30,  4, 365,  1,   680),
            ('Pred',          '5mg',         'Prednisolone',          'Hormones',       'Al-Habib',  'PRD005',    35,   18,  300, 30, 365, 20,   650),
            ('Pred',          '25mg',        'Prednisolone',          'Hormones',       'Al-Habib',  'PRD025',    75,   38,  200, 20, 365, 20,  1400),
            ('Dexamethasone', '0.5mg',       'Dexamethasone',         'Hormones',       'Zaka',      'DEX005',    45,   22,  250, 25, 365, 20,   850),
            ('Dexamethasone', '4mg',         'Dexamethasone',         'Hormones',       'Zaka',      'DEX040',    85,   42,  200, 20, 365, 20,  1600),

            # ── Injections ────────────────────────────────────────────────────
            ('Novaclox',      'Inj 500mg',   'Cloxacillin Inj',       'Injections',     'MedPharma', 'NVC001',   120,   60,   80,  8, 300,  1,   120),
            ('Rantidin',      'Inj 50mg',    'Ranitidine Inj',        'Injections',     'Rex',       'RNT001',    65,   32,  100, 10, 300,  1,    65),
            ('Decadron',      'Inj 8mg',     'Dexamethasone Inj',     'Injections',     'Sami',      'DCD001',    85,   42,  100, 10, 300,  1,    85),
            ('Adrenaline',    '1mg/ml',      'Epinephrine Inj',       'Injections',     'MedPharma', 'ADR001',   120,   60,   50,  5, 300,  1,   120),
            ('Hespan',        '500ml',       'HES 6% 500ml',          'Injections',     'Al-Habib',  'HSP001',   480,  240,   30,  5, 300,  1,   480),
            ('Normal Saline', '500ml',       'NaCl 0.9%',             'Injections',     'Rex',       'NSL001',   120,   60,   50,  5, 300,  1,   120),
            ('Dextrose',      '5% 500ml',    'Dextrose 5%',           'Injections',     'Zaka',      'DXT001',   130,   65,   50,  5, 300,  1,   130),

            # ── Misc / OTC ────────────────────────────────────────────────────
            ('Burnol',        'Cream',       'Framycetin+Cera',       'Dermatology',    'Al-Habib',  'BRN001',   120,   60,  150, 15, 720,  1,   120),
            ('Savlon',        'Liquid',      'Chlorhexidine',         'Dermatology',    'Rex',       'SVL001',   180,   90,  120, 12, 720,  1,   180),
            ('Disprin',       '300mg',       'Aspirin Soluble',       'Analgesics',     'MedPharma', 'DSP300',    35,   18,  300, 30, 730, 12,   400),
            ('Lactulose',     'Syrup',       'Lactulose',             'Gastro',         'Sami',      'LCT001',   220,  110,  100, 10, 400,  1,   220),
            ('Duphalac',      '15ml Sachet', 'Lactulose',             'Gastro',         'MedPharma', 'DPH001',   280,  140,   80,  8, 400, 10,  2700),
            ('ORS',           'Sachet',      'Oral Rehydration Salts','Gastro',         'Rex',       'ORS001',    30,   15,  400, 40, 730, 20,   550),
            ('Pedialyte',     'Sachet',      'Electrolyte Mix',       'Gastro',         'Al-Habib',  'PDL001',    55,   28,  300, 30, 540, 10,   520),
        ]

        count = 0
        for brand, strength, generic, cat_name, sup_key, barcode, sale, cost, qty, reorder, exp_days, pcs, pack in drugs:
            drug, created = Drug.objects.get_or_create(
                brand_name=brand, strength=strength,
                defaults=dict(
                    generic_name=generic,
                    category=cat(cat_name),
                    supplier=sup(sup_key),
                    barcode=barcode,
                    sale_price=sale,
                    cost_price=cost,
                    pieces_per_pack=pcs,
                    pack_price=pack,
                    quantity=qty,
                    reorder_level=reorder,
                    expiry_date=today + timedelta(days=exp_days),
                    is_active=True,
                )
            )
            if not created:
                drug.pieces_per_pack = pcs
                drug.pack_price = pack
                drug.save(update_fields=['pieces_per_pack', 'pack_price'])
            count += 1

        self.stdout.write(f'  [OK] Drugs ({count} records seeded)')

    def seed_customers(self):
        from apps.sales.models import Customer
        customers = [
            ('Ahmed Raza',    '0300-1112233', 'ahmed.raza@gmail.com',   'House 5, Gulberg, Lahore'),
            ('Fatima Malik',  '0333-2223344', 'fatima.malik@gmail.com', 'Flat 3B, DHA Phase 5, Lahore'),
            ('Tariq Mehmood', '0312-3334455', '',                       'Shop 22, Anarkali, Lahore'),
            ('Sana Javed',    '0345-4445566', 'sana.javed@hotmail.com', 'G-11, Islamabad'),
            ('Imran Sheikh',  '0321-5556677', '',                       'Saddar, Rawalpindi'),
            ('Nadia Akhtar',  '0311-6667788', 'nadia@email.pk',         'Clifton, Karachi'),
        ]
        for name, phone, email, address in customers:
            Customer.objects.get_or_create(
                name=name,
                defaults=dict(phone=phone, email=email, address=address)
            )
        self.stdout.write('  [OK] Customers (6)')

    def seed_purchases(self):
        from apps.inventory.models import Purchase, PurchaseItem, Drug, Supplier
        from apps.accounts.models import User

        if Purchase.objects.exists():
            self.stdout.write('  [SKIP] Purchases (already exist)')
            return

        pharmacist = (User.objects.filter(role='pharmacist').first()
                      or User.objects.filter(is_superuser=True).first())
        today = date.today()

        for i in range(5):
            sup   = Supplier.objects.order_by('?').first()
            drugs = list(Drug.objects.order_by('?')[:5])
            p = Purchase.objects.create(
                supplier=sup, pharmacist=pharmacist,
                invoice_no=f'PO-{2024000 + i}',
                status='received',
                purchase_date=today - timedelta(days=i * 7),
            )
            total = 0
            for drug in drugs:
                qty = random.randint(20, 60)
                PurchaseItem.objects.create(
                    purchase=p, drug=drug, quantity=qty,
                    cost_price=drug.cost_price,
                    expiry_date=today + timedelta(days=365),
                )
                total += qty * float(drug.cost_price)
            p.total_amount = total
            p.save(update_fields=['total_amount'])
        self.stdout.write('  [OK] Purchases (5 received POs)')

    def seed_sales(self):
        from apps.sales.models import Sale, SaleItem, Customer
        from apps.inventory.models import Drug
        from apps.accounts.models import Counter, User

        if Sale.objects.exists():
            self.stdout.write('  [SKIP] Sales (already exist)')
            return

        counters  = list(Counter.objects.filter(is_active=True))
        customers = list(Customer.objects.all())
        drugs     = list(Drug.objects.filter(is_active=True, quantity__gt=5))
        cashiers  = list(User.objects.filter(role='cashier'))

        if not counters or not drugs:
            self.stdout.write('  [WARN] No counters or drugs -- skipping sales')
            return

        today = timezone.now().date()
        total_sales = 0

        for days_ago in range(30):
            sale_date = today - timedelta(days=days_ago)
            num_sales = random.randint(3, 9)

            for _ in range(num_sales):
                counter  = random.choice(counters)
                cashier  = counter.cashier or (cashiers[0] if cashiers else None)
                customer = random.choice(customers) if random.random() > 0.4 else None
                chosen   = random.sample(drugs, k=random.randint(1, 4))
                payment  = random.choice(['cash', 'cash', 'cash', 'card', 'credit'])

                subtotal = 0
                items_data = []
                for drug in chosen:
                    qty = random.randint(1, 3)
                    subtotal += float(drug.sale_price) * qty
                    items_data.append((drug, qty))

                discount = round(subtotal * random.choice([0, 0, 0, 0.05, 0.10]), 2)
                total    = max(subtotal - discount, 0)
                paid     = total + random.choice([0, 0, 0, 50, 100])
                change   = max(paid - total, 0)

                dt = timezone.make_aware(
                    timezone.datetime.combine(sale_date, timezone.datetime.min.time())
                ) + timedelta(hours=random.randint(9, 20), minutes=random.randint(0, 59))

                sale = Sale.objects.create(
                    counter=counter, cashier=cashier, customer=customer,
                    payment_method=payment,
                    subtotal=subtotal, discount_amount=discount,
                    total_amount=total, amount_paid=paid, change_amount=change,
                    status='completed', sale_date=dt,
                )
                for drug, qty in items_data:
                    SaleItem.objects.create(
                        sale=sale, drug=drug,
                        quantity=qty, unit_price=drug.sale_price,
                    )
                    if days_ago <= 7:
                        drug.quantity = max(drug.quantity - qty, 0)
                        drug.save(update_fields=['quantity'])

                total_sales += 1

        self.stdout.write(f'  [OK] Sales ({total_sales} sales across last 30 days)')
