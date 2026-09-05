from lumyn.modules.rendez_vous.calendrier_ui import creer_html_calendrier


def test_html_echappe_et_limite_affichage():
    evenements=[{'titre':'<script>danger</script>','date':'2026-09-08','heure':'10h00'}]*4
    html=creer_html_calendrier(2026,9,evenements)
    assert '<script>' not in html
    assert html.count('&lt;script&gt;')==3
    assert '+1 autre(s)' in html


def test_evenement_autre_mois_non_affiche_sur_mauvais_jour():
    html=creer_html_calendrier(2026,9,[{'titre':'Autre mois','date':'2026-08-08','heure':None}])
    assert 'Autre mois' not in html
