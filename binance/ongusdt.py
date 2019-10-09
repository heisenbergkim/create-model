
from djongo import models
from pymongo import UpdateOne
from typing import List, Tuple

from coin.models.transaction import Transaction
from utils.time import align_date, now


class TransactionBinanceONGUSDT(models.Model):
    _id = models.ObjectIdField()

    e = models.CharField(verbose_name='거래소명', max_length=15)
    cu = models.CharField(verbose_name='화폐', max_length=10)
    f = models.CharField(verbose_name='기축화폐', max_length=10)

    id = models.IntegerField(verbose_name='체결id')
    is_ask = models.IntegerField(verbose_name='매도매수여부')
    p = models.FloatField(verbose_name='체결가')
    v = models.FloatField(verbose_name='거래량')
    t = models.IntegerField(verbose_name='타임스탬프')

    objects = models.DjongoManager()

    class Meta:
        verbose_name = verbose_name_plural = 'TransactionBinanceONGUSDT'
        indexes = [
            models.Index(fields=['t'], name='timestamp'),
            models.Index(fields=['e', 'cu', 'f'], name='exch_curr_fiat')
        ]
        unique_together = ('e', 'cu', 'f', 't')
        ordering = ['-t']

    def __str__(self):
        return f'{self.e}/{self.cu}_{self.f} ({self.t})'

    @classmethod
    def upsert(cls, e, cu, f, transaction):
        return cls.objects.mongo_update({
            'e': e.lower(),
            'cu': cu.lower(),
            'f': f.lower(),
            't': transaction['t']
        }, {'$set': dict(e=e.lower(), cu=cu.lower(), f=f.lower(), **transaction)}, upsert=True)

    @classmethod
    def bulk_upsert(cls, e, cu, f, Transactions):
        operations = [
            UpdateOne({
                'e': e.lower(),
                'cu': cu.lower(),
                'f': f.lower(),
                't': transaction['t']
            }, {'$set': dict(e=e.lower(), cu=cu.lower(), f=f.lower(), **transaction)}, upsert=True)
            for transaction in Transactions
        ]
        return cls.objects.mongo_bulk_write(operations, ordered=False)

    @classmethod
    def latest(cls, e, cu, f):
        now_date = now()
        t = int(now_date.timestamp())
        # aligned_t = int(align_date(now_date, i).timestamp())
        try:
            prev_candle = cls.objects.filter(e=e, cu=cu, f=f).first()
            open_price = prev_candle.c
        except:
            open_price = 0

        return cls(e=e, cu=cu, f=f, **Transaction.objects.aggregate(
            exchange=e, currency=cu, fiat=f,
            from_ts=aligned_t, until_ts=t, open_price=open_price)
        )

