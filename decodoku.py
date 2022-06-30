from qiskit_textbook.games.qiskit_game_engine import QiskitGameEngine
from qiskit_qec.decoders import DecodingGraph
from random import random, choice
from retworkx.visualization import mpl_draw
from distinctipy import distinctipy


class Decodoku():
    
    def __init__(self, p=0.1, k=2, L=10, process=None):
        
        self.p = p
        self.k = k
        self.L = L
        self.process = process

        self.d = L-1
        self.T = L+1
        
        self.generate_syndrome()
        self.generate_graph()

        
    def generate_syndrome(self):
        
        syndrome = {}
        for x in range(self.L):
            for y in range(self.L):
                syndrome[x,y] = 0
        
        error_num = 1
        for _ in range(2*self.L**2):
            error_num += random()<self.p
        for _ in range(error_num):
            x0 = choice(range(self.L))
            y0 = choice(range(self.L))
            if choice([True,False]):
                dx = []
                if x0>0:
                    dx.append(-1)
                if x0<(self.L-1):
                    dx.append(+1)
                x1 = x0 + choice(dx)
                y1 = y0
            else:
                dy = []
                if y0>0:
                    dy.append(-1)
                if y0<(self.L-1):
                    dy.append(+1)
                x1 = x0
                y1 = y0 + choice(dy)
            if x0 not in [0, self.L-1] or x1 not in [0, self.L-1]:
                e = choice(range(1,self.k))
                syndrome[x0,y0] += e
                syndrome[x1,y1] += self.k-e

        # generate colours for clusters
        input_colors = [(0,0,1), (1,2/3,0), (1,1,1), (0,0,0)]
        output_colors = distinctipy.get_colors(error_num, input_colors)
        self.error_colors = []
        for color in output_colors:
            hcolor = '#'
            for c in color:
                hc = hex(int(255*c))[2::]
                if len(hc)==1:
                    hc = '0'+hc
                hcolor += hc
            self.error_colors.append(hcolor)
        
        # compute boundary parities and scrub their syndromes
        parity = [0,0]
        for e,x in enumerate([0,self.L-1]):
            for y in range(self.L):
                parity[e] += syndrome[x,y]
                syndrome[x,y] = 0
            parity[e] = parity[e]%self.k
        self.boundary_errors = parity

        self.syndrome = syndrome
        self.original_syndrome = syndrome.copy()
        self.boundary_errors = parity
                
    def generate_graph(self):
        
        dg = DecodingGraph(None)
        dg.graph
        
        d = self.L-1

        pos = []
        for x in range(1,self.L-1):
            for y in range(self.L):
                e = x-1
                t = self.L-1-y
                dg.graph.add_node({'time':t, 'element':e, 'is_boundary':False})
                pos.append((e,-t))
        for e in [0,1]:
            dg.graph.add_node({'time':0, 'element':e, 'is_boundary':True})
            pos.append((d*(e==1) -2*(e==0), -(self.L-1)/2))

        nodes = dg.graph.nodes()
        # connect edges to boundary nodes
        for y in range(self.L):
            t = y
            n0 = nodes.index({'time':0, 'element':0, 'is_boundary':True})
            n1 = nodes.index({'time':t, 'element':0, 'is_boundary':False})
            dg.graph.add_edge(n0, n1, None)
            n0 = nodes.index({'time':0, 'element':1, 'is_boundary':True})
            n1 = nodes.index({'time':t, 'element':d-2, 'is_boundary':False})
            dg.graph.add_edge(n0, n1, None)
        # connect bulk nodes with space-like edges
        for y in range(self.L):
            for x in range(1,self.L-2):
                t = y
                e = x-1
                n0 = nodes.index({'time':t, 'element':e, 'is_boundary':False})
                n1 = nodes.index({'time':t, 'element':e+1, 'is_boundary':False})
                dg.graph.add_edge(n0, n1, None)
        # connect bulk nodes with time-like edges
        for y in range(self.L-1):
            for x in range(1,self.L-1):
                t = y
                e = x-1
                n0 = nodes.index({'time':t, 'element':e, 'is_boundary':False})
                n1 = nodes.index({'time':t+1, 'element':e, 'is_boundary':False})
                dg.graph.add_edge(n0, n1, None)
                
        self.decoding_graph = dg
        self.graph_pos = pos
        self.update_graph()

    def update_graph(self, original=False):

        for node in self.decoding_graph.graph.nodes():
            node['highlighted'] = False
            if self.k!=2:
                node['value'] = 0

        if original:
            syndrome = self.original_syndrome
        else:
            syndrome = self.syndrome
        
        highlighted_color = []
        for node in self.decoding_graph.graph.nodes():
            if node['is_boundary']:
                highlighted_color.append('orange')
            else:
                x = node['element']+1
                y = node['time']
                if (syndrome[x,y]%self.k)>0:
                    highlighted_color.append('red')
                    node['value'] = syndrome[x,y]%self.k
                    node['highlighted'] = True
                else:
                    highlighted_color.append('cornflowerblue')
        self.node_color = highlighted_color

    def start(self, engine):
        
        p = self.p
        d = self.k
        syndrome = self.syndrome

        # set edges to orange
        for x in [0, engine.L-1]:
            for y in range(engine.L):
                engine.screen.pixel[x,y].set_text('')
                engine.screen.pixel[x,y].set_color('orange')

        # set bulk to blue
        for x in range(1,engine.L-1):
            for y in range(engine.L):
                engine.screen.pixel[x,y].set_text('')
                engine.screen.pixel[x,y].set_color('blue')

        # display changed syndromes
        for x in range(1,engine.L-1):
            for y in range(engine.L):
                if syndrome[x,y]%d!=0:
                    if x not in [0, engine.L-1]:
                        if d!=2:
                            engine.screen.pixel[x,y].set_text(str(syndrome[x,y]%d))
                        engine.screen.pixel[x,y].set_color('red')

        engine.screen.pixel['text'].set_text('Choose node with an error')



    # this is the function that does everything
    def next_frame(self, engine):
        
        d = self.k
        syndrome = self.syndrome

        if len(engine.pressed_pixels)==1:
            (x,y) = engine.pressed_pixels[0]
            if x not in [0,engine.L-1] and syndrome[x,y]>0:
                engine.screen.pixel['text'].set_text('Choose node to move it to')
            else:
                engine.pressed_pixels = []
        elif len(engine.pressed_pixels)==2:
            # if we have a node and somewhere to move it to, then move it
            [(x0,y0), (x1,y1)] = engine.pressed_pixels
            if (x0,y0)!=(x1,y1):
                syndrome[x1,y1] += syndrome[x0,y0]
                syndrome[x0,y0] = 0
                for x,y in [(x0,y0), (x1,y1)]:
                    if syndrome[x,y]%d==0:
                        if x not in [0,engine.L-1]:
                            engine.screen.pixel[x,y].set_text('')
                            engine.screen.pixel[x,y].set_color('blue')
                    else:
                        if x not in [0,engine.L-1]:
                            if d!=2:
                                engine.screen.pixel[x,y].set_text(str(syndrome[x,y]%d))
                            engine.screen.pixel[x,y].set_color('red')

                engine.pressed_pixels = []
                engine.screen.pixel['text'].set_text('Choose syndrome element')
            else:
                engine.pressed_pixels = [(x0,y0)]

        else:
            engine.pressed_pixels = []
            engine.screen.pixel['text'].set_text('Choose syndrome element')

        if engine.controller['next'].value:
            engine.pressed_pixels = []
            engine.screen.pixel['text'].set_text('Choose syndrome element')

        # see how many non-trivial syndromes are left
        num_elems = 0
        for x in range(1,engine.L-1):
            for y in range(engine.L):
                num_elems += syndrome[x,y]%d

        if num_elems==0:
            parity = [0,0]
            for e,x in enumerate([0,engine.L-1]):
                for y in range(engine.L):
                    parity[e] += syndrome[x,y]
                parity[e] = parity[e]%d
                self.boundary_corrections = parity
            for e,x in enumerate([0,engine.L-1]):
                engine.screen.pixel[x,0].set_text(str(self.boundary_errors[e]))
                engine.screen.pixel[x,self.L-1].set_text(str(self.boundary_corrections[e]))
                
            if (self.boundary_corrections[0]+self.boundary_errors[0])%d==0:
                engine.screen.pixel['text'].set_text('Correction successful! :D')
                for y in range(engine.L):
                    for x in [0,engine.L-1]:
                        engine.screen.pixel[x,y].set_color('green')
            else:
                engine.screen.pixel['text'].set_text('Correction unsuccessful! :(')
                for y in range(engine.L):
                    for x in [0,engine.L-1]:
                        engine.screen.pixel[x,y].set_color('red')

            if engine.controller['next'].value:
                self.generate_syndrome()
                engine.start(engine)

        self.update_graph()

    def draw_graph(self, original=False, clusters=True):
        if self.process and clusters:
            parity, clusters = self.process(self)
        else:
            parity, clusters = None, None

        node_color = self.node_color.copy()
        nodes = self.decoding_graph.graph.nodes()
        if clusters:
            for n, c in clusters.items():
                node_color[n] = self.error_colors[c]       
        
        def get_label(node):
            if node['is_boundary'] and parity:
                return str(parity[node['element']])
            elif node['highlighted'] and 'value' in node and self.k!=2:
                return str(node['value'])
            else:
                return ''

        return mpl_draw(
            self.decoding_graph.graph,
            pos=self.graph_pos,
            node_color=node_color,
            labels=get_label,
            with_labels=True)

    def run(self):
        return QiskitGameEngine(self.start,self.next_frame,L=self.L,active_screen=True)