import os
import json
import datetime

import requests
import numpy as np


def somme_second(paire):
    return sum(paire[1])


class Portefeuille:
    """
    Représente un portefeuille d'actions sur lequel on peut effectuer des transactions et
    des analyses.
    """
    URL = "https://python.gel.ulaval.ca/action/{symbol}/historique"
    FORMAT_DATE = "%Y-%m-%d"

    def __init__(self, nom):
        self.nom = nom
        self.data = None
        self.charger_donnees()

    def deposer(self, montant, date_str):
        """Ajoute une opération de dépôt au portefeuille"""
        if date_str not in self.data['depots'].keys():
            self.data['depots'][date_str] = []
        self.data['depots'][date_str].append(montant)

    def acheter(self, qte, titres, date_str):
        """Ajoute des opérations d'achat au portefeuille pour chaque titre concerné"""
        self._ajouter_titres(titres)
        for titre in titres:
            if titre not in self.data['achats'].keys():
                self.data['achats'][titre] = {}
            if date_str not in self.data['achats'][titre].keys():
                self.data['achats'][titre][date_str] = []
            self.data['achats'][titre][date_str].append(qte)

    def vendre(self, qte, titres, date_str):
        """Ajoute des opérations de vente au portefeuille pour chaque titre concerné"""
        self._ajouter_titres(titres)
        for titre in titres:
            if titre not in self.data['ventes'].keys():
                self.data['ventes'][titre] = {}
            if date_str not in self.data['ventes'][titre].keys():
                self.data['ventes'][titre][date_str] = []
            self.data['ventes'][titre][date_str].append(qte)

    def solde(self, date_str):
        solde = 0
        for date_key, depots_date in self.data['depots'].items():
            if date_key <= date_str:
                solde += sum(depots_date)
        for titre in self.data['titres']:
            achats = self._achats_action(titre, date_str)
            ventes = self._ventes_action(titre, date_str)
            for date_achat, liste_achats in achats:
                prix = self.valeur([titre], date_achat)
                qte = sum(liste_achats)
                solde -= prix * qte
            for date_vente, liste_ventes in ventes:
                prix = self.valeur([titre], date_vente)
                qte = sum(liste_ventes)
                solde += prix * qte
        return solde

    def actions(self, titres, date_str):
        """Retourner les quantités d'actions de chaque titre dans le portefeuille"""
        return {titre: self._nb_actions(titre, date_str) for titre in titres}

    def titres(self):
        """Retourne les titres présents dans le portefeuille"""
        return self.data['titres']

    def _ajouter_titres(self, titres):
        # Vérifie les titres
        list(map(self._get_action, titres))
        # ajoute aux titres présents
        self.data['titres'].extend(titres)
        self.data['titres'] = list(set(self.data['titres']))

    def _nb_actions(self, titre, date_str):
        achats = self._achats_action(titre, date_str)
        ventes = self._ventes_action(titre, date_str)
        return sum(map(somme_second, achats)) - sum(map(somme_second, ventes))

    def _achats_action(self, titre, date_str):
        achats = []
        if titre in self.data['achats'].keys():
            for date_key, achats_date in self.data['achats'][titre].items():
                if date_key <= date_str:
                    achats.append((date_key, achats_date))
        return achats

    def _ventes_action(self, titre, date_str):
        ventes = []
        if titre in self.data['ventes'].keys():
            for date_key, ventes_date in self.data['ventes'][titre].items():
                if date_key <= date_str:
                    ventes.append((date_key, ventes_date))
        return ventes

    def _get_action(self, titre):
        url = self.URL.format(symbol=titre)
        res = requests.get(url).json()
        if "historique" not in res.keys():
            raise ValueError("Ce symbole est invalide: {}.".format(titre))
        return res

    def valeur(self, titres, date_str):
        """Retourne la valeur totale des titres données à une date donnée"""
        valeur_totale = 0
        if len(titres) > 0:
            if date_str not in self._get_action(titres[0])["historique"].keys():
                raise ValueError("Cette date n'est pas dans l'historique des titres demandés.")
        for titre in titres:
            donnees = self._get_action(titre)
            valeur_totale += donnees["historique"][date_str]["fermeture"]
        return valeur_totale

    def projections(self, rendement_moyen, volatilite, date_str):
        """Retourne 3 quartiles de la valeur projetée à une date ultérieure"""
        n = 10000
        date = self._str_to_date(date_str)
        dist_rend = np.random.normal(rendement_moyen, volatilite, n)
        quartiles = np.percentile(dist_rend, [25, 50, 75])
        valeur = 50
        duree = date - datetime.date.today()
        annees = int(duree.days / 365)
        jours = duree.days % 365
        return tuple(valeur * ((1 + quartiles / 100)**annees + jours / 365 * quartiles / 100))

    def charger_donnees(self):
        """Charge, s'il existe, le fichier de données de ce portefeuille"""
        fichier = os.path.join(os.getcwd(), '{}.json'.format(self.nom))
        if os.path.exists(fichier):
            with open(fichier, 'r') as f:
                self.data = self._valider_fichier(f)
        else:
            self.data = {'depots': {}, 'titres': [], 'ventes': {}, 'achats': {}}

    def sauver_donnees(self):
        """Sauvegarde le fichier de données de ce portefeuille"""
        fichier = os.path.join(os.getcwd(), '{}.json'.format(self.nom))
        with open(fichier, 'w') as f:
            json.dump(self.data, f)

    def _valider_fichier(self, f):
        """Valide et retourne les données du fichier de sauvegarde"""
        exc = Exception("Les données de ce portefeuille sont corrompues."
                        " Supprimez la sauvegarde.")
        try:
            data = json.load(f)
        except ValueError:
            raise exc
        try:
            data['depots'], data['titres'], data['ventes'], data['achats']
        except KeyError:
            raise exc
        return data

    def _str_to_date(self, date_str):
        try:
            return datetime.datetime.strptime(date_str, self.FORMAT_DATE).date()
        except ValueError:
            raise ValueError('Date mal formatée.')


class PortefeuilleGraphique(Portefeuille):
    """Un Portefeuille qui intègre le tracé de graphique"""

    def tracer_projections(self, rendement_moyen, volatilite, date):
        n = 10000
        dist_rend = np.random.normal(rendement_moyen, volatilite, n)
        quartiles = np.percentile(dist_rend, [25, 50, 75])
        valeur = 50
        duree = date - datetime.date.today()
        annees = int(duree.days/365)
        jours = duree.days % 365
        trimestres = int(duree.days/90)
