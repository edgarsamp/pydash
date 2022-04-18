from operator import indexOf
from numpy import Infinity
from r2a.ir2a import IR2A
from player.parser import *
from statistics import mean
import time
import math


class R2Adynamicsegmentsizeselection(IR2A):

    def __init__(self, id):
      IR2A.__init__(self, id)

      self.throughputs = []     # Vazoes  
      self.request_time = 0     # 
      self.qi = []              # Qualidades
      self.selected_qi = []
      self.a = [-1]
      self.m = 10
      

    def handle_xml_request(self, msg):
      self.request_time = time.perf_counter() # Salva o tempo em que a mensagem foi requisitada
      self.send_down(msg)


    def handle_xml_response(self, msg):
      
      parsed_mpd = parse_mpd(msg.get_payload())
      self.qi = parsed_mpd.get_qi()

      rtt = time.perf_counter() - self.request_time # Tempo para receber a mensagem
      self.throughputs.append(msg.get_bit_length() / (rtt/float(2)))

      # definindo o SS como a pior possivel, pois não sabemos o desenpenho da rede
      self.selected_qi.append(self.qi[0])

      self.send_up(msg)




    def handle_segment_size_request(self, msg):
      self.request_time = time.perf_counter()

      media_throughputs = mean(self.throughputs)

      peso = 0
      for i, throughput in enumerate(self.throughputs):
        peso += (i + 1) * abs(throughput - media_throughputs) / len(self.throughputs)

      # P é a probabilidade de mudar de qualidade, quanto mais perto de 1 mais estavel é a coneçao
      p = media_throughputs / (media_throughputs + peso)

      ss = 0 # last qi index
      for i, qi in enumerate(self.qi):
          if qi == self.selected_qi[-1]:
              ss = i
              break

      # t = tau, vontade de diminuir o SS
      t = (1 - p)*(max(0, max(0, ss-1)))

      # o = teta, vontade de aumentar o SS
      o = p*min(19, min(19, ss+1))



      #next_qi_index = temp_qualitys.index(min(temp_qualitys)) # mudar nome

      next_qi_index = round(self.qi.index(self.selected_qi[-1]) - t + o)

      # checa se esta passando dos limites de qualidades
      next_qi_index = max(0, next_qi_index)
      next_qi_index = min(19, next_qi_index)
      # Adiciona a qualidade escolhida no historico
      self.selected_qi.append(self.qi[next_qi_index])
      self.a.append(next_qi_index)
      



      print("-"*40)
      print('p', p)
      print('tau', t)
      print('teta', o)
      print('qi', self.qi)
      print('a', self.a[-1*self.m:])
      print('tam_throughputs', len(self.throughputs))
      print("-"*40)


      # Passa o indice da qualidade
      msg.add_quality_id(self.selected_qi[-1])

      self.send_down(msg)


    def handle_segment_size_response(self, msg):
      # Calcula o novo throughput
      rtt = time.perf_counter() - self.request_time
      self.throughputs.append(msg.get_bit_length() / (rtt/float(2)))

      # So guarda os ultimos 10 throughputs
      if(len(self.throughputs) > self.m):
        self.throughputs.pop(0)

      self.send_up(msg)






    def initialize(self):
      pass

    def finalization(self):
      pass