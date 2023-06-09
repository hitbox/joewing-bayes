# Utility for experimenting with Bayesian networks.
# Joe Wingbermuehle
# 2012-03-30

# Updated to Python 3
# Carl Harris
# 2023-04-10

import math
import random

import tkinter as tk

class BayesNode:
    """
    A node in a Bayes net.
    """

    def __init__(self, item, textItem, name, x, y):
        self.item = item
        self.textItem = textItem
        self.name = name
        self.x = x
        self.y = y
        self.parents = []
        self.children = []
        self.prob = dict()

    def addChild(self, node, line):
        """
        Add a child node connected by line.
        Returns false if this is an invalid connection.
        """
        if node == self:
            return False
        for (n, l) in self.children:
            if n == node:
                return False
        self.children += [(node, line)]
        return True

    def addParent(self, node, line):
        """
        Add a parent node connected by line.
        """
        for (n, l) in self.parents:
            if n == node:
                print("failed to addParent")
        self.parents += [(node, line)]

    def removeChild(self, node):
        """
        Remove child node.
        """
        self.children = [(c, l) for (c, l) in self.children if c != node]

    def removeParent(self, node):
        """
        Remove parent node.
        """
        self.parents = [(p, l) for (p, l) in self.parents if p != node]

    def isChild(self, node):
        """
        Determine if node is a child of this node.
        """
        return node in [c for (c, l) in self.children]

    def isParent(self, node):
        """
        Determine if node is a parent of this node.
        """
        return node in [p for (p, l) in self.parents]

    def getProbability(self, evidence):
        """
        Look up a probability in the probability table given evidence.
        """
        evalue = 0
        index = 1
        for (p, l) in self.parents:
            if p.name in evidence:
                evalue += index
            index *= 2
        if evalue in self.prob:
            return self.prob[evalue]
        else:
            return 0.5

    def draw(self, evidence):
        """
        Draw a sample given evidence.
        """
        pTrue = self.getProbability(evidence)
        return random.random() < pTrue

    def computeProbability(self, values):
        """
        Compute the probability of changing states.
        """
        pTrue = self.getProbability(values)
        if self.name in values:
            result = 1.0 - pTrue
        else:
            result = pTrue
        for (c, l) in self.children:
            pTrue = c.getProbability(values)
            if c.name in values:
                result *= 1.0 - pTrue
            else:
                result *= pTrue
        return result


class IndependenceChecker:
    """
    Class to check for independence among two nodes in a Bayes net.
    """

    def __init__(self, nodes, query, evidence):
        self.nodes = dict()
        for n in nodes.values():
            self.nodes[n.name] = n
        evidence = [abs(n) for n in evidence]
        query = [abs(n) for n in query]
        valid = len(query) == 2
        for n in query:
            if not self.nodes.has_key(n):
                valid = False
        if not valid:
            tkMessageBox.showwarning("Bad Input", "Invalid query.")
            return
        for n in evidence:
            if not self.nodes.has_key(n):
                valid = False
        if not valid:
            tk.messagebox.showwarning("Bad Input", "Invalid evidence.")
            return
        a = query.pop()
        b = query.pop()
        print(f"Checking independence of {a} and {b} given [{getListString(evidence)}]")
        result = self.checkIndependence(a, b, evidence)
        msg = f"Nodes {a} and {b} are "
        if result:
            title = "Independent"
            msg += "independent"
        else:
            title = "Dependent"
            msg += "dependent"
        if len(evidence) > 0:
            msg += " given " + getListString(evidence)
        msg += "."
        tk.messagebox.showinfo("Independent", msg)

    def getPaths(self, a, b):
        """
        Get a list of all undirected paths from a to b.
        """
        a, b = int(a), int(b)
        paths = []
        visited = set()
        queue = [(a, [a])]
        while len(queue) > 0:
            (node, path) = queue[0]
            queue = queue[1:]
            if node == b:
                paths.append(path)
            visited.add(node)
            for (n, l) in self.nodes[node].children + self.nodes[node].parents:
                if n.name not in visited:
                    queue += [(n.name, path + [n.name])]
        return paths

    def isCausalChain(self, a, b, c):
        """
        Determine if a, b, c forms a causal chain.
        """
        if self.nodes[a].isChild(self.nodes[b]) and \
            self.nodes[b].isChild(self.nodes[c]):
            return True
        if self.nodes[a].isParent(self.nodes[b]) and \
            self.nodes[b].isParent(self.nodes[c]):
            return True
        return False

    def isCommonCause(self, a, b, c):
        """
        Determine if a, b, c is a common cause.
        """
        if self.nodes[a].isParent(self.nodes[b]) and \
            self.nodes[c].isParent(self.nodes[b]):
            return True
        return False

    def hasEvidence(self, n, evidence):
        """
        Determine if there is evidence for n or a child of n.
        """
        if n in evidence:
            return True
        for (c, l) in self.nodes[n].children:
            if self.hasEvidence(c.name, evidence):
                return True
        return False

    def isActive(self, a, b, c, evidence):
        """
        Determine if the path a, b, c given evidence is active.
        """
        if b in evidence:
            if self.isCausalChain(a, b, c):
                print("\t\t-> causal chain with evidence (inactive)")
                return False
            if self.isCommonCause(a, b, c):
                print("\t\t-> common cause with evidence (inactive)")
                return False
        else:
            if self.isCausalChain(a, b, c):
                print("\t\t-> causal chain without evidence (active)")
                return True
            if self.isCommonCause(a, b, c):
                print("\t\t-> common cause without evidence (active)")
                return True

        # Must be common effect.
        # Check all children
        if self.hasEvidence(b, evidence):
            print("\t\t-> commmon effect with evidence (active)")
            return True
        else:
            print("\t\t-> commmon effect without evidence (inactive)")
            return False

    def checkPath(self, path, evidence):
        """
        Check if a path is active given evidence.
        """
        if len(path) >= 3:
            print(f"\tChecking path: {path}")
            x, y, z = path[0], path[1], path[2]
            if self.isActive(x, y, z, evidence):
                return self.checkPath(path[1:], evidence)
            else:
                return True    # Independent
        else:
            return False      # All active => dependent

    def checkIndependence(self, a, b, evidence):
        """
        Check if a and b are independent given evidence.
        """
        for path in self.getPaths(a, b):
            if not self.checkPath(path, evidence):
                return False
        return True


class ProbabilityDialog:
    """
    Class to prompt for probabilities.
    """

    def __init__(self, parent, node):
        self.node = node
        self.values = dict()
        self.top = tk.Toplevel(parent)
        self.top.transient(parent)
        self.top.minsize(256, 64)
        self.top.title(f"Probabilities for {node.name}")

        frame = tk.Frame(self.top)

        for (p, l) in node.parents:
            label = tk.Label(frame, text=str(p.name), width=3)
            label.pack(side=tk.LEFT)
        parents = [p.name for (p, l) in node.parents]
        prob = getQueryString([node.name], parents)
        probStr = tk.StringVar()
        probStr.set(prob)
        label = tk.Entry(frame, textvariable=probStr, state=DISABLED,
                      width=10, disabledforeground="black")
        label.pack(side=tk.LEFT)
        frame.pack()

        for p in range(0, 1 << len(node.parents)):
            frame = tk.Frame(self.top)
            for i in range(0, len(node.parents)):
                if (p & (1 << i)) != 0:
                    label = tk.Label(frame, text="T", width=3)
                else:
                    label = tk.Label(frame, text="F", width=3)
                label.pack(side=tk.LEFT)
            prob = 0.5
            if p in node.prob:
                prob = node.prob[p]
            var = tk.StringVar()
            var.set(str(prob))
            self.values[p] = var
            entry = tk.Entry(frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT)
            frame.pack(side=tk.TOP)

        frame = tk.Frame(self.top)
        b = tk.Button(frame, text="OK", command=self.ok)
        b.pack(side=tk.LEFT)
        b = tk.Button(frame, text="Cancel", command=self.cancel)
        b.pack(side=tk.LEFT)
        frame.pack(side=tk.TOP)

    def ok(self):
        try:
            for i in range(0, 1 << len(self.node.parents)):
                self.node.prob[i] = float(self.values[i].get())
        except ValueError:
            tk.messagebox.showwarning("Bad Input", "Values must be floats.")
        self.cancel()

    def cancel(self):
        self.top.destroy()


class Sampler:
    """
    Base class for sampling a Bayes net.
    """

    def __init__(self, parent, query, evidence, iterations, nodes):
        self.nodes = nodes
        self.query = query
        self.evidence = evidence
        self.iterations = iterations
        self.top = tk.Toplevel(parent)
        self.top.transient(parent)
        self.width = 320
        self.height = 240
        self.canvas = tk.Canvas(self.top, width=self.width, height=self.height)
        self.message = tk.StringVar()
        frame = tk.Frame(self.top)
        label = tk.Label(frame, textvariable=self.message, width=32)
        self.message.set("Working...")
        button = tk.Button(frame, text="Close", command=self.top.destroy)
        self.canvas.pack(side=tk.TOP)
        label.pack(side=tk.LEFT)
        button.pack(side=tk.LEFT)
        frame.pack(side=tk.TOP)

    def sample(self):
        """
        Method to perform sampling.
        """
        print("sample not implemented")

    def run(self, sampleFunction):
        """
        Sample using the specified function.
        """
        numerator = 0
        denominator = 0
        sampleValues = []
        for i in range(0, self.iterations):
            (weight, sample) = sampleFunction()
            print(f"\tSample: [{getListString(sample)}] weight: {weight}")
            if self.matches(sample, self.evidence):
                if self.matches(sample, self.query):
                    numerator += weight
                    print("(qmatch)")
                denominator += weight
                print("(ematch)")
                if denominator > 0:
                    sampleValues += [float(numerator) / float(denominator)]
            print(f"=> {numerator} / {denominator}")
        if denominator == 0:
            self.message.set("No samples matched the evidence.")
        else:
            result = str(float(numerator) / float(denominator))
            msg = getQueryString(self.query, self.evidence)
            msg += " = "+ result
            self.message.set(msg)
        sampleCount = len(sampleValues)
        self.canvas.create_text(16, 8, text="1.0")
        self.canvas.create_text(16, self.height - 8, text="0.0")
        xscale = float(self.width - 32) / float(sampleCount)
        yscale = float(self.height - 4) / 1.0
        x = 32
        for s in sampleValues:
            y = max(2, (1.0 - s) * yscale)
            self.canvas.create_oval(x, y, x + 1, y + 1)
            x += xscale

    def matches(self, sample, values):
        """
        Determine if values matches a sample.
        """
        for v in values:
            if v > 0:
                if v not in sample:
                    return False
            else:
                if -v in sample:
                    return False
        return True

    def getReadyNodes(self, sampled):
        """
        Get nodes that are ready to be sampled.
        """
        readyNodes = []
        for n in self.nodes:
            if n.name not in sampled:
                ready = True
                for (p, l) in n.parents:
                    if p.name not in sampled:
                        ready = False
                        break
                if ready:
                    readyNodes += [n]
        return readyNodes


class RejectionSampler(Sampler):
    """
    Class to perform rejection sampling.
    """

    def __init__(self, parent, query, evidence, iterations, nodes):
        super().__init__(parent, query, evidence, iterations, nodes)
        self.top.title("Rejection Sampler")
        self.sample()

    def sample(self):
        print(f"Collecting {self.iterations} samples using rejection sampling")
        self.run(self.forwardSample)

    def forwardSample(self):
        """
        Draw a sample using forward sampling.
        The function that calls this function will do the rejection.
        """
        sampled = set()
        values = []
        queue = self.getReadyNodes(sampled)
        while len(queue) > 0:
            node = queue[0]
            queue = queue[1:]
            inode = node.name
            if inode not in sampled:
                if node.draw(values):
                    values += [inode]
                sampled.add(inode)
                queue += self.getReadyNodes(sampled)
        return (1, values)


class LikelihoodSampler(Sampler):
    """
    Class to perform likelihood weighted sampling.
    """

    def __init__(self, parent, query, evidence, iterations, nodes):
        super().__init__(parent, query, evidence, iterations, nodes)
        self.top.title("Likelihood-Weighted Sampler")
        self.sample()

    def sample(self):
        print(f"Collecting {self.iterations} samples using likelihood sampling")
        self.run(self.likelihoodSample)

    def likelihoodSample(self):
        """
        Draw a sample using likelihood sampling.
        """
        sampled = set()
        values = []
        queue = self.getReadyNodes(sampled)
        weight = 1.0
        while len(queue) > 0:
            node = queue[0]
            queue = queue[1:]
            if node.name not in sampled:
                if node.name in self.evidence:
                    weight *= node.getProbability(values)
                    values += [node.name]
                elif -node.name in self.evidence:
                    weight *= 1.0 - node.getProbability(values)
                else:
                    if node.draw(values):
                        values += [node.name]
                sampled.add(node.name)
                queue += self.getReadyNodes(sampled)
        return (weight, values)


class GibbsSampler(Sampler):

    def __init__(self, parent, query, evidence, iterations, nodes):
        super().__init__(parent, query, evidence, iterations, nodes)
        self.top.title("Gibbs Sampler")

        # Set all values to the evidence and sample.
        self.state = [e for e in evidence if e > 0]
        evars = [abs(e) for e in evidence]
        self.variables = [n for n in nodes if n.name not in evars]
        self.sample()

    def sample(self):
        print(f"Collecting {self.iterations} samples using Gibbs samples")
        self.run(self.gibbsSample)

    def gibbsSample(self):
        """
        Draw a sample using Gibbs sampling.
        """

        # Pick a value to change and change it.
        node = random.choice(self.variables)
        if random.random() < node.computeProbability(self.state):
            if node.name not in self.state:
                self.state.append(node.name)
            elif node.name in self.state:
                self.state.remove(node.name)

        return (1, self.state)


class Network:
    """
    Class to allow construction of a Bayes net.
    """

    def __init__(self, master):
        self.size = 32
        self.startx = 0
        self.starty = 0
        self.nodes = dict()
        self.freeNames = []
        self.nextName = 1
        self.master = master
        frame = tk.Frame(master)
        selectFrame = tk.Frame(frame)
        queryFrame = tk.Frame(frame)
        buttonFrame = tk.Frame(frame)
        self.mode = tk.IntVar()
        self.mode.set(1)
        rb1 = tk.Radiobutton(selectFrame, text="Create/Move",
                          variable=self.mode, value=1,
                          command=self.changeMode)
        rb1.pack(side=tk.LEFT)
        rb2 = tk.Radiobutton(selectFrame, text="Connect",
                          variable=self.mode, value=2,
                          command=self.changeMode)
        rb2.pack(side=tk.LEFT)
        rb3 = tk.Radiobutton(selectFrame, text="Remove",
                          variable=self.mode, value=3,
                          command=self.changeMode)
        rb3.pack(side=tk.LEFT)
        rb4 = tk.Radiobutton(selectFrame, text="Probabilities",
                          variable=self.mode, value=4,
                          command=self.changeMode)
        rb4.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(frame, width=640, height=480, bg="gray")
        self.canvas.bind("<Button-1>", self.push)
        self.canvas.bind("<B1-Motion>", self.motion)
        self.canvas.bind("<ButtonRelease-1>", self.release)

        self.message = tk.StringVar()
        msg = tk.Label(frame, textvariable=self.message)
        self.changeMode()

        l = tk.Label(queryFrame, text="Query: ")
        l.pack(side=tk.LEFT)
        self.query = tk.Entry(queryFrame, width=5, validate=tk.ALL,
                           vcmd=self.updateQuery)
        self.query.pack(side=tk.LEFT)
        l = tk.Label(queryFrame, text="Evidence: ")
        l.pack(side=tk.LEFT)
        self.evidence = tk.Entry(queryFrame, width=8, validate=tk.ALL,
                              vcmd=self.updateQuery)
        self.evidence.pack(side=tk.LEFT)
        l = tk.Label(queryFrame, text="Iterations: ")
        l.pack(side=tk.LEFT)
        it = tk.StringVar()
        vc = (master.register(self.validateIterations), '%S')
        self.iterations = tk.Entry(queryFrame, width=6, textvariable=it,
                                validate=tk.ALL, vcmd=vc)
        self.iterations.pack(side=tk.LEFT)
        it.set("100")
        b = tk.Button(buttonFrame, text="Dependent?",
                   command=self.checkIndependence)
        b.pack(side=tk.LEFT)
        b = tk.Button(buttonFrame, text="Sample (LWS)", command=self.sampleLWS)
        b.pack(side=tk.LEFT)
        b = tk.Button(buttonFrame, text="Sample (Gibbs)", command=self.sampleGibbs)
        b.pack(side=tk.LEFT)
        b = tk.Button(buttonFrame, text="Sample (Rejection)", command=self.sampleRS)
        b.pack(side=tk.LEFT)
        b = tk.Button(buttonFrame, text="Exit", command=self.exit)
        b.pack(side=tk.LEFT)

        selectFrame.pack(side=tk.TOP)
        msg.pack(side=tk.TOP)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        queryFrame.pack(side=tk.TOP)
        buttonFrame.pack(side=tk.TOP)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

    def updateQuery(self):
        """
        Highlight nodes.
        This is called when the query or evidence changes.
        """
        qvalues = parseNodes(self.query.get())
        evalues = parseNodes(self.evidence.get())
        for n in self.nodes.values():
            if (n.name in qvalues) or (-n.name in qvalues):
                self.canvas.itemconfig(n.item, fill="green")
            elif n.name in evalues:
                self.canvas.itemconfig(n.item, fill="blue")
            elif -n.name in evalues:
                self.canvas.itemconfig(n.item, fill="red")
            else:
                self.canvas.itemconfig(n.item, fill="black")
        return True

    def validateIterations(self, s):
        """
        Validate the iterations input.
        """
        if s == '':
            return True
        try:
            i = int(s)
            if i >= 0:
                return True
        except ValueError:
            pass
        return False

    def changeMode(self):
        """
        Change input modes.
        """
        mode = self.mode.get()
        if mode == 1:
            self.message.set("Click to create or drag to move")
        elif mode == 2:
            self.message.set("Drag to connect")
        elif mode == 3:
            self.message.set("Click to remove")
        elif mode == 4:
            self.message.set("Click to modify probabilities")

    def push(self, event):
        """
        Button push.
        """
        mode = self.mode.get()
        if mode == 1:
            self.select(event)
        elif mode == 2:
            self.startLine(event)
        elif mode == 3:
            self.remove(event)
        elif mode == 4:
            self.setProbabilities(event)

    def motion(self, event):
        """
        Mouse drag.
        """
        mode = self.mode.get()
        if mode == 1:
            self.move(event)
        elif mode == 2:
            self.updateLine(event)

    def release(self, event):
        """
        Mouse release.
        """
        mode = self.mode.get()
        if mode == 2:
            self.stopLine(event)

    def checkIndependence(self):
        """
        Check if the two nodes in the query are independent given the evidence.
        """
        query = parseNodes(self.query.get())
        evidence = parseNodes(self.evidence.get())
        d = IndependenceChecker(self.nodes, query, evidence)

    def sampleLWS(self):
        """
        Perform likelihood sampling for the query and evidence.
        """
        nodes = [n for n in self.nodes.values()]
        query = parseNodes(self.query.get())
        evidence = parseNodes(self.evidence.get())
        try:
            iterations = int(self.iterations.get())
        except ValueError:
            iterations = 100
        LikelihoodSampler(self.master, query, evidence, iterations, nodes)

    def sampleGibbs(self):
        """
        Perform Gibbs sampling for the query and evidence.
        """
        nodes = [n for n in self.nodes.values()]
        query = parseNodes(self.query.get())
        evidence = parseNodes(self.evidence.get())
        try:
            iterations = int(self.iterations.get())
        except ValueError:
            iterations = 100
        GibbsSampler(self.master, query, evidence, iterations, nodes)

    def sampleRS(self):
        """
        Perform rejection sampling for the query and evidence.
        """
        nodes = [n for n in self.nodes.values()]
        query = parseNodes(self.query.get())
        evidence = parseNodes(self.evidence.get())
        try:
            iterations = int(self.iterations.get())
        except ValueError:
            iterations = 100
        RejectionSampler(self.master, query, evidence, iterations, nodes)

    def exit(self):
        """
        Exit the program.
        """
        self.master.destroy()

    def setProbabilities(self, event):
        """
        Set probabilities for the selected node.
        """
        self.startx = self.canvas.canvasx(event.x) - self.size / 2
        self.starty = self.canvas.canvasy(event.y) - self.size / 2
        items = self.canvas.find_overlapping(self.startx, self.starty,
                                             self.startx + self.size,
                                             self.starty + self.size)
        for i in items:
            if i in self.nodes:
                p = ProbabilityDialog(self.master, self.nodes[i])
                return

    def getName(self):
        """
        Get the next available node name.
        """
        if len(self.freeNames) > 0:
            name = self.freeNames[0]
            self.freeNames = self.freeNames[1:]
        else:
            name = self.nextName
            self.nextName += 1
        return name

    def releaseName(self, name):
        """
        Release a node name so it can be reused.
        """
        self.freeNames += [name]
        list.sort(self.freeNames)

    def createNode(self, x, y):
        """
        Create a node.
        """
        name = self.getName()
        item = self.canvas.create_oval(x, y, x + self.size, y + self.size,
                                       fill="black")
        ti = self.canvas.create_text(x + self.size / 2, y + self.size / 2,
                                     fill="white", text=str(name))
        node = BayesNode(item, ti, name, x, y)
        self.nodes[item] = node
        return item

    def select(self, event):
        """
        Select or create a node.
        """
        offset = self.size / 2
        x = self.canvas.canvasx(event.x) - offset
        y = self.canvas.canvasy(event.y) - offset
        items = self.canvas.find_overlapping(x, y, x + self.size, y + self.size)
        self.selection = None
        for i in items:
            if i in self.nodes:
                self.selection = i
        if self.selection == None:
            self.selection = self.createNode(x, y)
        node = self.nodes[self.selection]
        self.canvas.move(node.item, x - node.x, y - node.y)
        self.canvas.move(node.textItem, x - node.x, y - node.y)
        node.x, node.y = x, y
        for (n, l) in node.parents:
            self.drawLine(l, n, node)
        for (n, l) in node.children:
            self.drawLine(l, node, n)
        self.startx = x
        self.starty = y

    def move(self, event):
        """
        Move a node.
        """
        offset = self.size / 2
        x = self.canvas.canvasx(event.x) - offset
        y = self.canvas.canvasy(event.y) - offset
        item = self.selection
        node = self.nodes[item]
        self.canvas.move(item, x - self.startx, y - self.starty)
        self.canvas.move(node.textItem, x - self.startx, y - self.starty)
        self.startx, self.starty = x, y
        node.x, node.y = x, y
        for (n, l) in node.parents:
            self.drawLine(l, n, node)
        for (n, l) in node.children:
            self.drawLine(l, node, n)

    def drawLine(self, line, a, b):
        """
        Move a line to connect node a to b.
        """
        offset = self.size / 2
        x, y = b.x + offset, b.y + offset
        angle = math.atan2(b.y - a.y, b.x - a.x)
        x1, y1 = a.x + offset, a.y + offset
        x2 = b.x + offset - offset * math.cos(angle)
        y2 = b.y + offset - offset * math.sin(angle)
        self.canvas.coords(line, (x1, y1, x2, y2))

    def startLine(self, event):
        """
        Start forming a connection.
        """
        self.startx = self.canvas.canvasx(event.x) - self.size / 2
        self.starty = self.canvas.canvasy(event.y) - self.size / 2
        items = self.canvas.find_overlapping(self.startx, self.starty,
                                             self.startx + self.size,
                                             self.starty + self.size)
        item = None
        for i in items:
            if i in self.nodes:
                item = i
        if item == None:
            item = self.createNode(self.startx, self.starty)
        self.startNode = self.nodes[item]
        self.line = self.canvas.create_line(self.startNode.x + self.size / 2,
                                            self.startNode.y + self.size / 2,
                                            self.startx + self.size / 2,
                                            self.starty + self.size / 2,
                                            arrow=tk.LAST)
        self.canvas.tag_lower(self.line)

    def updateLine(self, event):
        """
        Update the line for a connection.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        c = self.canvas.coords(self.line)
        c = c[0], c[1], x, y
        self.canvas.coords(self.line, c)

    def stopLine(self, event):
        """
        Finish a connection.
        """
        offset = self.size / 2
        x = self.canvas.canvasx(event.x) - offset
        y = self.canvas.canvasy(event.y) - offset
        items = self.canvas.find_overlapping(x, y, x + self.size, y + self.size)
        item = None
        for i in items:
            if i in self.nodes:
                item = i
        if item == None:
            item = self.createNode(x, y)
        node = self.nodes[item]
        if self.startNode.addChild(node, self.line):
            node.addParent(self.startNode, self.line)
        else:
            self.canvas.delete(self.line)
            return
        self.drawLine(self.line, self.startNode, node)

    def remove(self, event):
        """
        Remove the selected node.
        """
        x = self.canvas.canvasx(event.x) - self.size / 2
        y = self.canvas.canvasy(event.y) - self.size / 2
        items = self.canvas.find_overlapping(x, y, x + self.size, y + self.size)
        item = None
        for i in items:
            if i in self.nodes:
                item = i
        if item != None:
            node = self.nodes[item]
            self.canvas.delete(node.textItem)
            self.releaseName(node.name)
            for (c, l) in node.children:
                self.canvas.delete(l)
                c.removeParent(node)
            for (p, l) in node.parents:
                self.canvas.delete(l)
                p.removeChild(node)
            self.canvas.delete(item)
            self.nodes.pop(item)

def getListString(values):
    """
    Get a string representation of a list of numbers.
    """
    return ",".join(map(str, values))

def parseNodes(nodes):
    """
    Parse a list of nodes.
    """
    result = set()
    for n in nodes.split():
        for s in n.split(","):
            try:
                i = int(s)
                result.add(i)
            except ValueError:
                print(f"Could not part '{s}'")
    return result

def getQueryString(query, evidence):
    """
    Get a string representation of a query given evidence.
    """
    queryString = getListString(query)
    if len(evidence) > 0:
        evidenceString = getListString(evidence)
        return f"P({queryString}|{evidenceString})"
    else:
        return f"P({queryString})"

root = tk.Tk()
root.title("Bayes")
network = Network(root)
root.mainloop()
