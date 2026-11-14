# -*- coding: utf-8 -*-
# The script, slide by slide. Replace all of it. This example is entirely fictional:
# the brand, the sector, every figure and every quote are invented to show the format.
# One slide = one idea. Read references/03-content-format.md and references/02-copywriting.md first.
from vsl import s, b, q, v

CTX = 'Exemple fictif · salle de sport'
VERBATIM = 'Verbatim fictif du modèle. Dans une vraie VSL, citez les mots exacts de votre étude de marché.'

BARS = dict(a=dict(label='En mars', share=.33, value='12 inscriptions'),
            b=dict(label='En janvier', share=.67, extra=.33, value='24 à 36 inscriptions'))
BOARD = [['Mardi 18 h', 'À rappeler'], ['Jeudi 12 h', 'Ensuite'], ['Hors zone', 'Non']]
CURVES = dict(slow='Réputation', fast='Méthode', axis='Temps')
PILLARS = [['Être vu', 'eye'], ['Être trouvé', 'pin'], ['Être choisi', 'phone']]
STACK = ['Annonces créées et pilotées', 'Formulaire de tri', 'Fiche Google reprise',
         'Demandes sur votre téléphone', 'Tableau chaque lundi', 'Deux séances de préparation']
BONUS = [['grid', '10 formats', 'publicitaires'], ['coin', 'Votre coût', 'par inscription'], ['web', 'Votre page', 'refaite, offerte']]
TWIN_A = ['Budget publicitaire', 'À partir de 20 € par jour', 'Réglé à la plateforme']
TWIN_B = ['Notre forfait', 'Annoncé avant tout engagement', 'Après vos inscriptions']

INTRO = [
    b('hook',
      s('Si vous dirigez une salle de sport indépendante, une question.', 'Salles de sport indépendantes.'),
      s('Combien de membres vous ont rejoint ce mois-ci *sans que vous baissiez vos prix* ?', 'Sans baisser vos prix ?')),
    b('promise',
      s('Je vais vous montrer comment signer *trente nouveaux membres en soixante jours*.', '30 membres. 60 jours.'),
      s('Sans promotion. Sans vous filmer. Même si tout repose aujourd’hui sur le bouche-à-oreille.', 'Sans promotion. Sans vous filmer.')),
    b('pain',
      s('Janvier vous remplit. Puis « *la salle se vide dès le mois de mars* ».', 'La salle se vide en mars.', note=VERBATIM),
      s('Dans notre exemple, mars compte *douze inscriptions*.', '12 inscriptions.', v=v('bars', two=False, **BARS)),
      s('Janvier en comptait *vingt-quatre à trente-six*.', '24 à 36 en janvier.', v=v('bars', two=True, **BARS))),
    b('proof',
      s('Je suis Prénom, fondateur de Votre Marque. Oui, mon bureau est mal rangé.', 'Prénom, fondateur.'),
      s('Notre équipe a accompagné *quarante salles*.', '40 salles.', stats=[('40', 'salles accompagnées')], context=CTX)),
    b('plan',
      s('Voici ce qui a changé, notre méthode, puis vos questions.', 'Ce qui a changé. La méthode. Vos questions.')),
    b('picture',
      s('Imaginez votre lundi matin. Trois essais réservés, *dans votre quartier*, à votre tarif.', 'Lundi matin.', v=v('board', cards=BOARD, lit=False, tag='Exemple')),
      s('Vous savez qui rappeler en premier. Et vous pouvez enfin *refuser une promotion*.', 'Vous pouvez refuser.', v=v('board', cards=BOARD, lit=True, tag='Exemple'))),
]

OLD_NEW = [
    b('old',
      s('Pendant des années, *on parlait de vous*.', 'On parlait de vous.'),
      s('Le flyer. La promotion. Le bouche-à-oreille. Instagram.', 'Flyer. Promotion. Bouche-à-oreille.', v=v('pills', items=['Flyer', 'Promotion', 'Bouche-à-oreille', 'Instagram'])),
      s('Et les comparateurs, qui revendent *le même contact à dix salles*.', 'Le même contact. Dix salles.', v=v('fanout', **{'from': 'Un contact', 'you': 'Vous'}))),
    b('why',
      s('Votre réputation a construit votre salle. Gardez-la. Mais ces méthodes ont un défaut : *vous attendez*.', 'Vous attendez.', v=v('shift', left='Hier', right='Aujourd’hui', a='Le client', b='Vous')),
      s('Or votre futur membre ne cherche pas une salle. *Il veut se remettre en forme*.', 'Il veut se remettre en forme.'),
      s('Une vidéo. Les avis. Les horaires. Puis il réserve.', 'Vidéo. Avis. Horaires.', v=v('journey', steps=[['photo', 'Vidéo'], ['search', 'Avis'], ['clock', 'Horaires'], ['phone', 'Réservation']]))),
    b('shift',
      s('Vous en connaissez sûrement une. Une salle ouverte l’an dernier, déjà pleine le soir.', 'Ouverte l’an dernier.'),
      s('Or la réputation se compte en années.', 'La réputation se compte en années.', v=v('curves', two=False, **CURVES)),
      s('*Une méthode se compte en semaines.*', 'Une méthode se compte en semaines.', v=v('curves', two=True, **CURVES)),
      s('Cette salle se montre avant qu’on la cherche. Elle trie. Elle rappelle vite.', 'Se montrer. Trier. Rappeler.', v=v('numbers', items=['Se montrer', 'Trier', 'Rappeler vite']))),
    b('new',
      s('Un relais, c’est ce qui *amène le client jusqu’à votre porte*.', 'Jusqu’à votre porte.', v=v('road')),
      s('Voici la *méthode Relais*. Trois piliers, installés en soixante-douze heures.', 'La méthode Relais.', v=v('pillars', items=PILLARS, on=0)),
      s('Premier pilier : *être vu*. Vos cours, devant votre quartier.', 'Être vu.', v=v('pillars', items=PILLARS, on=1)),
      s('Deuxième pilier : *être trouvé*. Une fiche Google complète, avec vos vrais avis.', 'Être trouvé.', v=v('pillars', items=PILLARS, on=2)),
      s('Troisième pilier : *être choisi*. La demande arrive sur votre téléphone. *Vous rappelez sous cinq minutes*.', 'Être choisi.', v=v('phone', notif=['Nouvelle', 'demande'], big='5 min', caption='C’est vous qui rappelez')),
      s('Cela a l’air simple. Voici vos questions.', 'Vos questions.')),
]

FAQ = [
    q('Encore des curieux ?',
      [s('« Ils viennent pour l’essai gratuit *et ils disparaissent*. »', 'Ils disparaissent.', note=VERBATIM)],
      [s('Ce qui vous coûte du temps, c’est l’absence de tri.', 'L’absence de tri.')],
      [s('Avec la méthode Relais, *vous fixez vos critères* : quartier, horaires, budget minimum.', 'Vos critères.', v=v('filter', label='Vos critères')),
       s('Vous lisez chaque demande avant d’appeler. Et vous gardez *le droit de dire non*.', 'Le droit de dire non.'),
       s('Avant de réserver, chacun indique son objectif, son quartier, son budget et ses horaires.', 'Objectif. Quartier. Budget.', v=v('card', title='Nouvelle demande', tag='Exemple', rows=[['Objectif', 'Reprendre le sport'], ['Quartier', 'Dans votre zone'], ['Budget annoncé', 'Dans vos critères'], ['Horaires', 'Après 18 h']]))],
      [s('Dans notre exemple, *seize demandes sur vingt* sont venues à leur essai.', '16 sur 20.', stats=[('16 / 20', 'demandes venues à leur essai')], context=CTX)],
      kind='quality'),
    q('Je n’ai pas le temps.',
      [s('« Je suis en salle toute la journée. Je n’ai pas le temps. »', 'Je n’ai pas le temps.')],
      [s('Vous n’avez pas le temps de faire de la publicité. Justement, vous n’en ferez pas.', 'Vous n’en ferez pas.')],
      [s('Nous gérons les annonces, la fiche Google et le suivi. Vous : *une heure pour démarrer*.', 'Une heure pour démarrer.', v=v('split', left=dict(title='Nous', items=['Annonces', 'Fiche Google', 'Formulaire et suivi']), right=dict(title='Vous', items=['Une heure, accès, photos', 'Relire les annonces', 'Rappeler, recevoir']))),
       s('Avec la méthode Relais, tout est en ligne *en soixante-douze heures*.', 'Tout est en ligne.', v=v('install', big='72 heures', steps=['Vos accès', 'Installation', 'En ligne']))],
      [s('Une salle de notre exemple a reçu sa première demande *en neuf jours*.', '9 jours.', stats=[('9 jours', 'entre le lancement et la première demande')], context=CTX)],
      kind='time'),
    q('Qu’est-ce que j’obtiens exactement ?',
      [s('« Concrètement, qu’est-ce que j’obtiens ? »', 'Qu’est-ce que j’obtiens ?')],
      [s('Une liste de prestations ne remplit aucune salle. Tout doit être relié.', 'Tout doit être relié.')],
      [s('Soixante jours de méthode Relais. Annonces, formulaire de tri, fiche Google.', '60 jours, tout compris.', v=v('stack', items=STACK, two=False)),
       s('Les demandes sur votre téléphone, un tableau chaque lundi, deux séances de préparation.', 'Rien à assembler.', v=v('stack', items=STACK, two=True)),
       s('Compte publicitaire, page et fiche : *tout reste à votre nom*.', 'Tout reste à votre nom.', v=v('owned', items=['Compte publicitaire', 'Page', 'Fiche Google'], caption='À votre nom')),
       s('Chaque lundi, quatre chiffres. Dépenses, demandes, essais, inscriptions.', 'Quatre chiffres.', v=v('dashboard', items=['Dépenses', 'Demandes', 'Essais', 'Inscriptions'])),
       s('Et pendant l’appel, vous repartez avec *trois documents offerts*.', 'Trois documents offerts.', v=v('cards', items=BONUS, on=0)),
       s('D’abord, *dix formats publicitaires* qui tournent déjà dans votre ville.', '10 formats publicitaires.', v=v('cards', items=BONUS, on=1))],
      [s('Notre équipe a déjà transmis *deux cent dix demandes*.', '210 demandes.', stats=[('210', 'demandes transmises')], context=CTX)],
      kind='offer'),
    q('Combien ça coûte ?',
      [s('« Ça va être trop cher pour moi. »', 'Trop cher pour moi ?')],
      [s('La bonne question, c’est ce que vous coûte un été à moitié vide.', 'Un été à moitié vide.')],
      [s('Deux montants. Votre budget publicitaire, *à partir de vingt euros par jour*, réglé à la plateforme.', 'Deux montants.', v=v('twin', a=TWIN_A, b=TWIN_B, both=False)),
       s('Et notre forfait, annoncé avant tout engagement, payable *après vos premières inscriptions*.', 'Après vos inscriptions.', v=v('twin', a=TWIN_A, b=TWIN_B, both=True))],
      [s('Dans notre exemple : *cinq euros encaissés pour un euro de publicité*.', '5 € pour 1 €.', stats=[('5 €', 'encaissés pour 1 € de publicité')], context=CTX)],
      kind='price'),
    q('Et si ça ne marche pas ?',
      [s('« Et si je m’engage, et qu’il ne se passe rien ? »', 'Et si ça ne marche pas ?')],
      [s('Sur ce marché, le risque est souvent pour vous. Ici, il est pour nous.', 'Ici, le risque est pour nous.')],
      [s('Avec la méthode Relais, l’objectif est écrit : trente membres en soixante jours.', 'Trente membres. 60 jours.', v=v('deadline', start='Jour 1', end='Jour 60', title='Trente nouveaux membres', sub='Dans les critères fixés au départ', tick=False)),
       s('*Sous dix inscriptions, vous ne payez pas notre forfait.* Le budget publicitaire reste réglé à la plateforme.', 'Vous ne payez pas.', v=v('deadline', start='Jour 1', end='Jour 60', title='Moins de dix inscriptions', sub='Vous ne payez pas notre forfait', tick=True), note='Exemple. Une garantie réelle se valide avec votre conseil juridique et doit exister au contrat.'),
       s('C’est écrit dans le contrat, que vous lisez *avant de vous engager*.', 'Écrit dans le contrat.', v=v('contract', lines=['Moins de dix inscriptions :', 'vous ne payez pas le forfait.']))],
      [s('Quarante salles accompagnées. *4,7 sur 5* sur Google.', '4,7 / 5.', stats=[('4,7 / 5', 'sur Google'), ('40', 'salles accompagnées')], context=CTX)],
      kind='guarantee'),
]

CTA = [
    b('action',
      s('Cliquez sur le bouton sous cette vidéo et réservez *votre appel offert*.', 'Réservez votre appel offert.', v=v('cta', question='Combien de membres actifs avez-vous aujourd’hui ?'))),
    b('question',
      s('En réservant, une seule question : *combien de membres actifs avez-vous aujourd’hui ?*', 'Combien de membres actifs ?', v=v('cta', question='Combien de membres actifs avez-vous aujourd’hui ?'), note='Cette question doit exister réellement dans le formulaire de réservation.'),
      s('Nous préparerons votre appel autour de votre réponse.', 'Un appel préparé pour vous.')),
]

PROOF = [
    b('salad',
      s('Salle A. *Vingt-huit inscriptions en soixante jours*, à quatorze euros la demande.', '28 inscriptions.', stats=[('28', 'inscriptions en 60 jours'), ('14 €', 'par demande')], who='Salle A', context=CTX),
      s('Salle B. *Trente-trois essais réservés* le premier mois.', '33 essais.', stats=[('33', 'essais réservés le premier mois')], who='Salle B', context=CTX),
      s('« Mes cours du soir sont pleins. *Je recommande*. » Prénom Nom, gérant.', '« Je recommande. »', who='Prénom Nom', context=CTX),
      s('Salle C, sans aucune promotion. *Onze jours* avant la première inscription.', '11 jours.', stats=[('11 jours', 'avant la première inscription')], who='Salle C', context=CTX),
      s('« Une équipe *à l’écoute*, qui répond vite. » Prénom Nom, gérante.', '« À l’écoute. »', who='Prénom Nom', context=CTX),
      s('Réservez *votre appel offert*, avec le bouton sous cette vidéo.', 'Réservez votre appel offert.')),
]
