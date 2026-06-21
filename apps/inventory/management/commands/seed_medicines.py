"""
Management command: python manage.py seed_medicines
Adds medicine catalog with 0 stock and 0 price.
Staff updates prices and stock when drugs are received from suppliers.
Drugs with 0 stock are inactive (hidden from POS) until stock is added.
Safe to run multiple times — skips existing records.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed medicine catalog with 0 stock and 0 price (inactive until stock received)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete all existing drugs before seeding')

    def handle(self, *args, **options):
        from apps.inventory.models import Drug, Category, Supplier

        if options['clear']:
            Drug.objects.all().delete()
            self.stdout.write('  Cleared all drugs.\n')

        def cat(name):
            obj, _ = Category.objects.get_or_create(name=name)
            return obj

        # brand_name, strength, generic_name, category
        medicines = [
            # ── Antibiotics ──────────────────────────────────────
            ('Amoxil',        '250mg',        'Amoxicillin',            'Antibiotics'),
            ('Amoxil',        '500mg',        'Amoxicillin',            'Antibiotics'),
            ('Augmentin',     '375mg',        'Amoxiclav',              'Antibiotics'),
            ('Augmentin',     '625mg',        'Amoxiclav',              'Antibiotics'),
            ('Flagyl',        '200mg',        'Metronidazole',          'Antibiotics'),
            ('Flagyl',        '400mg',        'Metronidazole',          'Antibiotics'),
            ('Ciprofloxacin', '250mg',        'Ciprofloxacin',          'Antibiotics'),
            ('Ciprofloxacin', '500mg',        'Ciprofloxacin',          'Antibiotics'),
            ('Erythrocin',    '250mg',        'Erythromycin',           'Antibiotics'),
            ('Erythrocin',    '500mg',        'Erythromycin',           'Antibiotics'),
            ('Doxycycline',   '100mg',        'Doxycycline',            'Antibiotics'),
            ('Klacid',        '250mg',        'Clarithromycin',         'Antibiotics'),
            ('Klacid',        '500mg',        'Clarithromycin',         'Antibiotics'),
            ('Septran',       'DS',           'Co-trimoxazole',         'Antibiotics'),
            ('Cefixime',      '200mg',        'Cefixime',               'Antibiotics'),
            ('Cefixime',      '400mg',        'Cefixime',               'Antibiotics'),
            ('Zinnat',        '250mg',        'Cefuroxime',             'Antibiotics'),
            ('Zinnat',        '500mg',        'Cefuroxime',             'Antibiotics'),

            # ── Analgesics ───────────────────────────────────────
            ('Panadol',       '500mg',        'Paracetamol',            'Analgesics'),
            ('Panadol',       'Extra',        'Paracetamol+Caffeine',   'Analgesics'),
            ('Panadol',       'Extend',       'Paracetamol SR',         'Analgesics'),
            ('Brufen',        '200mg',        'Ibuprofen',              'Analgesics'),
            ('Brufen',        '400mg',        'Ibuprofen',              'Analgesics'),
            ('Brufen',        '600mg',        'Ibuprofen',              'Analgesics'),
            ('Voltaren',      '25mg',         'Diclofenac',             'Analgesics'),
            ('Voltaren',      '50mg',         'Diclofenac',             'Analgesics'),
            ('Meftal',        '250mg',        'Mefenamic Acid',         'Analgesics'),
            ('Meftal',        '500mg',        'Mefenamic Acid',         'Analgesics'),
            ('Aspirin',       '300mg',        'Acetylsalicylic Acid',   'Analgesics'),
            ('Tramadol',      '50mg',         'Tramadol HCl',           'Analgesics'),
            ('Disprin',       '300mg',        'Aspirin Soluble',        'Analgesics'),

            # ── Antacids ─────────────────────────────────────────
            ('Gaviscon',      'Liquid',       'Alginate Antacid',       'Antacids'),
            ('Gaviscon',      'Tablets',      'Alginate Antacid',       'Antacids'),
            ('Histac',        '150mg',        'Ranitidine',             'Antacids'),

            # ── Gastro ───────────────────────────────────────────
            ('Nexium',        '20mg',         'Esomeprazole',           'Gastro'),
            ('Nexium',        '40mg',         'Esomeprazole',           'Gastro'),
            ('Omeprazole',    '20mg',         'Omeprazole',             'Gastro'),
            ('Losec',         '20mg',         'Omeprazole',             'Gastro'),
            ('Motilium',      '10mg',         'Domperidone',            'Gastro'),
            ('Flagyl',        '500mg Susp',   'Metronidazole Susp',     'Gastro'),
            ('Immodium',      '2mg',          'Loperamide',             'Gastro'),
            ('Lactulose',     'Syrup',        'Lactulose',              'Gastro'),
            ('Duphalac',      '15ml Sachet',  'Lactulose',              'Gastro'),
            ('ORS',           'Sachet',       'Oral Rehydration Salts', 'Gastro'),
            ('Pedialyte',     'Sachet',       'Electrolyte Mix',        'Gastro'),

            # ── Antihistamines ────────────────────────────────────
            ('Zyrtec',        '5mg',          'Cetirizine',             'Antihistamines'),
            ('Zyrtec',        '10mg',         'Cetirizine',             'Antihistamines'),
            ('Allegra',       '120mg',        'Fexofenadine',           'Antihistamines'),
            ('Allegra',       '180mg',        'Fexofenadine',           'Antihistamines'),
            ('Phenergan',     '10mg',         'Promethazine',           'Antihistamines'),
            ('Clarinase',     '5mg',          'Loratadine+Pseudo',      'Antihistamines'),
            ('Loratadine',    '10mg',         'Loratadine',             'Antihistamines'),

            # ── Vitamins ─────────────────────────────────────────
            ('Centrum',       'Silver',       'Multivitamin',           'Vitamins'),
            ('Centrum',       'Kids',         'Multivitamin Chewable',  'Vitamins'),
            ('Vitamin C',     '500mg',        'Ascorbic Acid',          'Vitamins'),
            ('Vitamin C',     '1000mg',       'Ascorbic Acid',          'Vitamins'),
            ('Vitamin D3',    '1000IU',       'Cholecalciferol',        'Vitamins'),
            ('Vitamin D3',    '5000IU',       'Cholecalciferol',        'Vitamins'),
            ('Omega-3',       '1000mg',       'Fish Oil',               'Vitamins'),
            ('Zinc Sulphate', '20mg',         'Zinc Sulphate',          'Vitamins'),
            ('Calcium',       '500mg',        'Calcium Carbonate',      'Vitamins'),
            ('Calcium',       '1000mg',       'Calcium Carbonate',      'Vitamins'),
            ('Folic Acid',    '5mg',          'Folic Acid',             'Vitamins'),
            ('Iron',          '150mg',        'Ferrous Sulphate',       'Vitamins'),

            # ── Cardiovascular ────────────────────────────────────
            ('Norvasc',       '5mg',          'Amlodipine',             'Cardiovascular'),
            ('Norvasc',       '10mg',         'Amlodipine',             'Cardiovascular'),
            ('Concor',        '2.5mg',        'Bisoprolol',             'Cardiovascular'),
            ('Concor',        '5mg',          'Bisoprolol',             'Cardiovascular'),
            ('Concor',        '10mg',         'Bisoprolol',             'Cardiovascular'),
            ('Cozaar',        '50mg',         'Losartan',               'Cardiovascular'),
            ('Cozaar',        '100mg',        'Losartan',               'Cardiovascular'),
            ('Atenolol',      '50mg',         'Atenolol',               'Cardiovascular'),
            ('Atenolol',      '100mg',        'Atenolol',               'Cardiovascular'),
            ('Simvastatin',   '20mg',         'Simvastatin',            'Cardiovascular'),
            ('Simvastatin',   '40mg',         'Simvastatin',            'Cardiovascular'),
            ('Aspirin',       '75mg',         'Acetylsalicylic Acid',   'Cardiovascular'),
            ('Digoxin',       '0.25mg',       'Digoxin',                'Cardiovascular'),

            # ── Diabetes ─────────────────────────────────────────
            ('Glucophage',    '500mg',        'Metformin',              'Diabetes'),
            ('Glucophage',    '850mg',        'Metformin',              'Diabetes'),
            ('Glucophage',    '1000mg',       'Metformin',              'Diabetes'),
            ('Amaryl',        '1mg',          'Glimepiride',            'Diabetes'),
            ('Amaryl',        '2mg',          'Glimepiride',            'Diabetes'),
            ('Amaryl',        '4mg',          'Glimepiride',            'Diabetes'),
            ('Lantus',        'SoloStar',     'Insulin Glargine',       'Diabetes'),
            ('Novorapid',     'FlexPen',      'Insulin Aspart',         'Diabetes'),
            ('Januvia',       '50mg',         'Sitagliptin',            'Diabetes'),
            ('Jardiance',     '10mg',         'Empagliflozin',          'Diabetes'),

            # ── Dermatology ──────────────────────────────────────
            ('Betnovate',     'Cream',        'Betamethasone',          'Dermatology'),
            ('Betnovate',     'Scalp',        'Betamethasone Solution', 'Dermatology'),
            ('Fusiderm',      'Cream',        'Fusidic Acid',           'Dermatology'),
            ('Canesten',      'Cream',        'Clotrimazole',           'Dermatology'),
            ('Canesten',      'Pessary',      'Clotrimazole 500mg',     'Dermatology'),
            ('Nizoral',       'Shampoo',      'Ketoconazole',           'Dermatology'),
            ('Nizoral',       'Cream',        'Ketoconazole',           'Dermatology'),
            ('Dermovate',     'Cream',        'Clobetasol',             'Dermatology'),
            ('Calamine',      'Lotion',       'Calamine',               'Dermatology'),
            ('Burnol',        'Cream',        'Framycetin+Cera',        'Dermatology'),
            ('Savlon',        'Liquid',       'Chlorhexidine',          'Dermatology'),

            # ── Cough & Cold ─────────────────────────────────────
            ('Benylin',       'Cough Syrup',  'Dextromethorphan',       'Cough & Cold'),
            ('Benylin',       'Dry Cough',    'Dextromethorphan DM',    'Cough & Cold'),
            ('Sinopharm',     'Cold Tab',     'Chlorphenamine',         'Cough & Cold'),
            ('Otrivin',       'Adult',        'Xylometazoline 0.1%',    'Cough & Cold'),
            ('Otrivin',       'Baby',         'Xylometazoline 0.05%',   'Cough & Cold'),
            ('Vicks',         'VapoRub',      'Camphor+Menthol',        'Cough & Cold'),
            ('Vicks',         'Inhaler',      'Menthol+Camphor',        'Cough & Cold'),
            ('Prospan',       'Syrup',        'Ivy Leaf Extract',       'Cough & Cold'),
            ('Mucosolvan',    'Syrup',        'Ambroxol',               'Cough & Cold'),
            ('Mucosolvan',    'Tablets',      'Ambroxol 30mg',          'Cough & Cold'),

            # ── Eye & Ear ────────────────────────────────────────
            ('Tobrex',        'Eye Drops',    'Tobramycin',             'Eye & Ear'),
            ('Otosporin',     'Ear Drops',    'Polymyxin',              'Eye & Ear'),
            ('Systane',       'Eye Drops',    'Polyethylene Glycol',    'Eye & Ear'),
            ('Voltaren',      'Eye Drops',    'Diclofenac 0.1%',        'Eye & Ear'),
            ('Chlorsig',      'Eye Drops',    'Chloramphenicol',        'Eye & Ear'),
            ('Waxsol',        'Ear Drops',    'Docusate Sodium',        'Eye & Ear'),
            ('Similasan',     'Eye Drops',    'Homeopathic',            'Eye & Ear'),

            # ── Respiratory ──────────────────────────────────────
            ('Ventolin',      'Inhaler',      'Salbutamol 100mcg',      'Respiratory'),
            ('Ventolin',      'Nebules',      'Salbutamol 2.5mg',       'Respiratory'),
            ('Seretide',      '25/50',        'Salmeterol+Fluticasone', 'Respiratory'),
            ('Seretide',      '25/125',       'Salmeterol+Fluticasone', 'Respiratory'),
            ('Singulair',     '5mg',          'Montelukast',            'Respiratory'),
            ('Singulair',     '10mg',         'Montelukast',            'Respiratory'),
            ('Atrovent',      'Inhaler',      'Ipratropium',            'Respiratory'),
            ('Theo-Asthalin', '100mg',        'Theophylline',           'Respiratory'),

            # ── Neurological ─────────────────────────────────────
            ('Depakine',      '200mg',        'Sodium Valproate',       'Neurological'),
            ('Depakine',      '500mg',        'Sodium Valproate',       'Neurological'),
            ('Tegretol',      '200mg',        'Carbamazepine',          'Neurological'),
            ('Rivotril',      '0.5mg',        'Clonazepam',             'Neurological'),
            ('Rivotril',      '2mg',          'Clonazepam',             'Neurological'),
            ('Lexotanil',     '1.5mg',        'Bromazepam',             'Neurological'),
            ('Inderal',       '40mg',         'Propranolol',            'Neurological'),
            ('Stugeron',      '25mg',         'Cinnarizine',            'Neurological'),
            ('Stugeron',      'Forte',        'Cinnarizine 75mg',       'Neurological'),

            # ── Hormones ─────────────────────────────────────────
            ('Eltroxin',      '50mcg',        'Levothyroxine',          'Hormones'),
            ('Eltroxin',      '100mcg',       'Levothyroxine',          'Hormones'),
            ('Proluton',      '250mg',        'Hydroxyprogesterone',    'Hormones'),
            ('Duphaston',     '10mg',         'Dydrogesterone',         'Hormones'),
            ('Clomid',        '50mg',         'Clomifene',              'Hormones'),
            ('Ovestin',       'Cream',        'Estriol',                'Hormones'),
            ('Pred',          '5mg',          'Prednisolone',           'Hormones'),
            ('Pred',          '25mg',         'Prednisolone',           'Hormones'),
            ('Dexamethasone', '0.5mg',        'Dexamethasone',          'Hormones'),
            ('Dexamethasone', '4mg',          'Dexamethasone',          'Hormones'),

            # ── Injections ───────────────────────────────────────
            ('Novaclox',      'Inj 500mg',    'Cloxacillin Inj',        'Injections'),
            ('Rantidin',      'Inj 50mg',     'Ranitidine Inj',         'Injections'),
            ('Decadron',      'Inj 8mg',      'Dexamethasone Inj',      'Injections'),
            ('Adrenaline',    '1mg/ml',       'Epinephrine Inj',        'Injections'),
            ('Hespan',        '500ml',        'HES 6% 500ml',           'Injections'),
            ('Normal Saline', '500ml',        'NaCl 0.9%',              'Injections'),
            ('Dextrose',      '5% 500ml',     'Dextrose 5%',            'Injections'),
        ]

        created = 0
        skipped = 0
        for brand, strength, generic, category_name in medicines:
            _, made = Drug.objects.get_or_create(
                brand_name=brand,
                strength=strength,
                defaults=dict(
                    generic_name=generic,
                    category=cat(category_name),
                    sale_price=0,
                    cost_price=0,
                    quantity=0,
                    reorder_level=10,
                    pieces_per_pack=1,
                    pack_price=0,
                    is_active=False,
                )
            )
            if made:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {created} medicines added, {skipped} already existed.\n'
            f'All new medicines are INACTIVE with 0 stock and 0 price.\n'
            f'They will activate automatically when stock is received.'
        ))
