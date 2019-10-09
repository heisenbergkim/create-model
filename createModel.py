# -*- coding: utf-8 -*-

import os
import sys
import csv
from jinja2 import Template


root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt  # noqa: E402


def style(s, style):
    return style + s + '\033[0m'


def green(s):
    return style(s, '\033[92m')


def blue(s):
    return style(s, '\033[94m')


def yellow(s):
    return style(s, '\033[93m')


def red(s):
    return style(s, '\033[91m')


def pink(s):
    return style(s, '\033[95m')


def bold(s):
    return style(s, '\033[1m')


def underline(s):
    return style(s, '\033[4m')


def dump(*args):
    print(' '.join([str(arg) for arg in args]))


def print_supported_exchanges():
    dump('Supported exchanges:', green(', '.join(ccxt.exchanges)))


data = '''
from djongo import models
from pymongo import UpdateOne
from typing import List, Tuple

from coin.models.transaction import Transaction
from utils.time import align_date, now


class Transaction{{name}}(models.Model):
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
        verbose_name = verbose_name_plural = 'Transaction{{name}}'
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


'''


try:

    id = sys.argv[1]  # get exchange id from command line arguments

    # check if the exchange is supported by ccxt
    exchange_found = id in ccxt.exchanges

    if exchange_found:
        dump('Instantiating', green(id), 'exchange')

        # instantiate the exchange by id
        exchange = getattr(ccxt, id)({
            # 'proxy':'https://cors-anywhere.herokuapp.com/',
        })

        # load all markets from the exchange
        markets = exchange.load_markets()

        # output a list of all market symbols
        dump(green(id), 'has', len(exchange.symbols),
             'symbols:', exchange.symbols)

        tuples = list(ccxt.Exchange.keysort(markets).items())
        # print(type(tuples))
        # print("Eric")

        # debug
        for (k, v) in tuples:
            # print(v)
            pass

        # output a table of all markets
        # dump(pink('{:<15} {:<15} {:<15} {:<15}'.format('id', 'symbol', 'base', 'quote')))

        for (k, v) in tuples:
            # dump(yellow('{:<15} {:<15} {:<15} {:<15}'.format(v['id'], v['symbol'], v['base'], v['quote'])))
            if v['quote'] == 'USDT':
                print(v['id'] + "," + v['symbol'] +
                      "," + v['base'] + "," + v['quote'])
                # todo something...
                mystr = "Binance" + v['id']
                tm = Template(data)
                msg = tm.render(name=mystr)
                # print(msg)

                data2 = "{{name}}.py"
                tm2 = Template(data2)
                fileName = tm2.render(name=v['id'])
                fileName = fileName.lower()

                print(fileName)

                f = open("/home/ericnjin/create-model/binance/" + fileName, 'w')
                f.write(msg)

        f.close()

    else:

        dump('Exchange ' + red(id) + ' not found')
        print_supported_exchanges()

except Exception as e:
    dump('[' + type(e).__name__ + ']', str(e))
    dump("Usage: python " + sys.argv[0], green('id'))
    # print_supported_exchanges()
