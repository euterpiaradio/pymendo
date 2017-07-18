# -*- coding: utf-8 -*-

import datetime
import locale
import urllib2
import requests
import pymendo


handler = urllib2.HTTPHandler(debuglevel=1)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)

headers = {
    'Authorization': 'Basic eWFubmljazp2dFVMT3JsZ2Zac3YwOTZuZjNnV2FFVDM='
}


def main():
    locale.setlocale(locale.LC_TIME, 'fr_CH.utf8')

    cursor = pymendo.db.cnx.cursor()
    sql = "SELECT MAX(c.weekly_key) FROM weekly_charts c"
    cursor.execute(sql)
    key = next(x for x in cursor)
    sql = ("SELECT @date:='%s-1', @from:=DATE_ADD(STR_TO_DATE(@date, '%%x-%%v-%%w'), INTERVAL -7 DAY), "
           "DATE_ADD(@from, INTERVAL 6 DAY), DATE_FORMAT(@from, '%%x-%%v')") % key[0]
    cursor.execute(sql)
    r = next(row for row in cursor)
    sow = datetime.datetime.strptime(r[1], '%Y-%m-%d')
    sow_d = sow.__format__("%d")
    sow_m = sow.__format__("%B")
    sow_y = sow.__format__("%Y")
    eow = datetime.datetime.strptime(r[2], '%Y-%m-%d')
    eow_d = eow.__format__("%d")
    eow_m = eow.__format__("%B")
    eow_y = eow.__format__("%Y")
    key = r[3]

    if sow_y != eow_y:
        titre = "Semaine du %s %s %s au %s %s %s" % (sow_d, sow_m, sow_y, eow_d, eow_m, eow_y)
    elif sow_m != eow_m:
        titre = "Semaine du %s %s au %s %s %s" % (sow_d, sow_m, eow_d, eow_m, eow_y)
    else:
        titre = "Semaine du %s au %s %s %s" % (sow_d, eow_d, eow_m, eow_y)
    print
    print titre
    print

    sql = ("SELECT CONCAT('|', c.position, '|', IF(p.progression < 0, p.progression, IF(p.progression > 0, "
           "CONCAT('+', p.progression), '-')), '|', CONCAT(c.artist_name, ' / ', c.track_name), '|', "
           "c.weekly_score, '|') FROM weekly_charts c LEFT JOIN weekly_progression p ON p.weekly_key = c.weekly_key "
           "AND p.track_id = c.track_id WHERE c.weekly_key = '%s' LIMIT 25") % key
    cursor.execute(sql)
    content = "|Pos.|Prog.|Artite / Titre|Score|\n"
    content += "|-:|-:|:-|-:|\n"
    for row in cursor:
        content += row[0] + "\n"
    print content
    print

    url = "http://localhost/er/wp-json/wp/v2/charts?slug=%s" % key
    response = requests.get(url, headers=headers)
    data = response.json()
    if len(data) == 0:
        print "Création de l'article"
        url = "http://localhost/er/wp-json/wp/v2/charts"
        requests.post(url, headers=headers, data={
            'title': titre,
            'slug': key,
            'status': 'publish',
            'content': content
        })
    else:
        print "Mise à jour de l'article"
        postid = data[0]['id']
        url = "http://localhost/er/wp-json/wp/v2/charts/%s" % postid
        requests.post(url, headers=headers, data={
            'title': titre,
            'status': 'publish',
            'content': content
        })