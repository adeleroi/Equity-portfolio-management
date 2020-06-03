import argparse
import datetime

from portefeuille import Portefeuille


class Gestionnaire:
    actions = (
        ("déposer", "Déposer la quantité de dollars spécifiée, à la date spécifiée"),
        ("acheter", "Acheter la quantité spécifiée des titres spécifiés, à la date spécifiée"),
        ("vendre", "Vendre la quantité spécifiée des titres spécifiés, à la date spécifiée"),
        ("solde", "Afficher en dollars le solde des liquidités, à la date spécifiée"),
        ("titres", ("Afficher les nombres d'actions détenues pour chacun"
                    " des titres spécifiés, à la date spécifiée; "
                    "affichez une ligne par titre, avec le format titre=quantité")),
        ("valeur", ("Afficher la valeur totale des titres spécifiés, à la date spécifiée;"
                    " affichez la valeur sur une ligne, en limitant l'affichage à 2 décimales")),
        ("projection", ("Projeter la valeur totale des titres spécifiés, à la"
                        "date future spécifiée, en tenant compte des rendements"
                        "et indices de volatilité spécifiés; affichez la"
                        "projection sur une seule ligne, en limitant"
                        "l'affichage de la valeur à 2 décimales"))
    )

    def extraire_arguments(self):
        parser = argparse.ArgumentParser(description="Gestionnaire de portefeuille d'actions")
        sous_commandes = parser.add_subparsers(title="ACTIONS", dest="commande")
        actions = self.actions
        for nom, description in actions:
            action_parser = sous_commandes.add_parser(nom, help=description)
            action_parser.add_argument("-d", "--date", dest="date", metavar="DATE", default=None)
            action_parser.add_argument(
                "-q", "--quantité", dest="qte", metavar="INT", default=1, type=int,
                help="Quantité désirée (par défaut: 1)")
            action_parser.add_argument(
                "-t", "--titres", dest="titres", metavar="STRING", nargs="+", default=None,
                help=("Le ou les titres à considérer "
                      "(par défaut, tous les titres du portefeuille sont considérés)"))
            action_parser.add_argument(
                "-r", "--rendement", dest="r", metavar="FLOAT", default=0, type=float,
                help="Rendement annuel global (par défaut, 0)")
            action_parser.add_argument(
                "-v", "--volatilité", dest="v", metavar="FLOAT", default=0, type=float,
                help="Indice de volatilité global sur le rendement annuel (par défaut, 0)")
            action_parser.add_argument(
                "-g", "--graphique", dest="graph", metavar="BOOL", default=False, type=bool,
                help="Affichage graphique (par défaut, pas d'affichage graphique)")
            action_parser.add_argument(
                "-p", "--portefeuille", dest="port", metavar="STRING", default="folio",
                help="Nom de portefeuille (par défaut, utiliser folio)")
        return parser.parse_args()

    def executer(self):
        args = self.extraire_arguments()
        cmd = args.commande
        args.date = datetime.date.today().strftime("%Y-%m-%d") if args.date is None else args.date
        port = Portefeuille(args.port)
        args.titres = args.titres or port.titres()

        if cmd == 'déposer':
            port.deposer(args.qte, args.date)
        elif cmd == 'acheter':
            port.acheter(args.qte, args.titres, args.date)
        elif cmd == 'vendre':
            port.vendre(args.qte, args.titres, args.date)
        elif cmd == 'solde':
            print('{:.2f}'.format(port.solde(args.date)))
        elif cmd == 'titres':
            actions = port.actions(args.titres, args.date)
            print('\n'.join(['{}={}'.format(t, q) for t, q in actions.items()]))
        elif cmd == 'valeur':
            print('{:.2f}'.format(port.valeur(args.titres, args.date)))
        elif cmd == 'projection':
            print(tuple('{:.2f}'.format(m) for m in port.projections(args.r, args.v, args.date)))
        port.sauver_donnees()


if __name__ == '__main__':
    gest = Gestionnaire()
    gest.executer()
