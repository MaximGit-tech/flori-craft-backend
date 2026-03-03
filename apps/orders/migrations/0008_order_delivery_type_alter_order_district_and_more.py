from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_telegramadmin'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_type',
            field=models.CharField(
                choices=[('delivery', 'Доставка'), ('pickup', 'Самовывоз')],
                default='delivery',
                max_length=10,
                verbose_name='Тип получения'
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='district',
            field=models.CharField(
                blank=True,
                choices=[
                    ('JK', 'ЖК Филиград, Онли, Береговой'),
                    ('FILI', 'Район Фили'),
                    ('MKAD', 'МКАД'),
                    ('NMKAD', 'За Мкадом'),
                ],
                null=True
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='full_address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='time',
            field=models.CharField(max_length=20),
        ),
    ]