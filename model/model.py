import copy

from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0


        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()
        #print(self.relazioni_punti_escursioni)


    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        lista_dict_relazioni_punti_escursioni=EscursioneDAO.get_escursioni_punti_interesse()
        for dict_relazioni_punti_escursioni in lista_dict_relazioni_punti_escursioni:
            key_escursione=dict_relazioni_punti_escursioni['id_escursione']
            key_punto_interesse=dict_relazioni_punti_escursioni['id_punto_interesse']
            escursione= self.escursioni_map.get(key_escursione)
            punto_interesse= self.punti_interesse_map.get(key_punto_interesse)
            if punto_interesse is not None and escursione is not None:
                escursione.punti_interesse.add(punto_interesse)
                punto_interesse.escursioni.add(escursione)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        punti_utilizzati=set()
        escursioni_parco=[]
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1
        for id_escursione in self.escursioni_map:
            if id_parco==self.escursioni_map.get(id_escursione).id_parco:
                escursioni_parco.append(self.escursioni_map.get(id_escursione))
        self._ricorsione(0,[],0,0,0,punti_utilizzati,max_giorni,max_budget,escursioni_parco)
        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def verifica_vincoli(self,max_budget,max_giorni,durata_corrente,costo_corrente,punti_usati,pacchetto_parziale,escursione):
        if punti_usati.intersection(escursione.punti_interesse)!=set():
            return False
        if max_budget is not None and costo_corrente+escursione.costo > max_budget:
            return False
        if max_giorni is not None and durata_corrente+escursione.durata_giorni > max_giorni:
            return False
        if escursione in pacchetto_parziale:
            return False
        return True

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set,max_giorni,max_budget,escursioni_parco):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""
        if self._valore_ottimo==-1 or self._valore_ottimo<valore_corrente:
                self._valore_ottimo=valore_corrente
                self._costo=costo_corrente
                self._pacchetto_ottimo=list(pacchetto_parziale)
        for start_index in range(start_index,len(escursioni_parco)):
                valore_corrente_nuovo = 0
                if self.verifica_vincoli(max_budget,max_giorni,durata_corrente,costo_corrente,punti_usati,pacchetto_parziale,escursioni_parco[start_index]):
                        pacchetto_parziale.append(escursioni_parco[start_index])
                        durata_corrente_nuova=escursioni_parco[start_index].durata_giorni
                        costo_corrente_nuovo=escursioni_parco[start_index].costo
                        nuovi_punti_usati = set(punti_usati)
                        for punti_interesse in escursioni_parco[start_index].punti_interesse:
                            valore_corrente_nuovo+=punti_interesse.voto_visitatori
                            nuovi_punti_usati.add(punti_interesse)
                        self._ricorsione((start_index+1),pacchetto_parziale,(durata_corrente+durata_corrente_nuova),(costo_corrente+costo_corrente_nuovo),(valore_corrente+valore_corrente_nuovo),nuovi_punti_usati,max_giorni,max_budget,escursioni_parco)
                        pacchetto_parziale.pop()
