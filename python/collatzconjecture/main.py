"""
Visualisation of the Collatz conjecture

Author: Sam Barba
Created 07/08/2023
"""

from graphviz import Digraph
import matplotlib.pyplot as plt


plt.rcParams['figure.figsize'] = (9, 6)


def do_collatz(num, print_trajectory):
	trajectory = [num]
	while num > 1:
		if print_trajectory: print(num, end='')
		if num % 2 == 0:
			num //= 2
			if print_trajectory: print(f' / 2 = {num}')
		else:
			num = 3 * num + 1
			if print_trajectory: print(f' * 3 + 1 = {num}')
		trajectory.append(num)
	return trajectory


if __name__ == '__main__':
	# 1. Plot trajectory for a single number

	num = 27
	trajectory = do_collatz(num, print_trajectory=True)
	plt.plot(trajectory, color='red', linewidth=1)
	plt.xlabel('Iteration')
	plt.ylabel('Value')
	plt.title(f'{len(trajectory) - 1} iterations for {num:,} to reach 1 (max value: {max(trajectory):,})')
	plt.show()

	# 2. Plot no. iterations per number, 1 to 10,000

	nums_and_iters = dict()

	for i in range(1, 10001):
		trajectory = do_collatz(i, print_trajectory=False)
		nums_and_iters[i] = len(trajectory) - 1

	plt.scatter(nums_and_iters.keys(), nums_and_iters.values(), color='red', s=1)
	plt.xlabel('Number')
	plt.ylabel('No. iters to reach 1')
	plt.title('Iterations per num')
	plt.show()

	# 3. Generate graph of trajectories of all numbers that take <= 15 steps to reach 1

	# See https://en.wikipedia.org/wiki/Collatz_conjecture#In_reverse
	# (function for generating trajectories in reverse)

	max_depth = 15
	nodes = [1]
	edges = dict()

	for _ in range(max_depth):
		for n in nodes[:]:
			new_n = 2 * n
			if new_n not in nodes:
				nodes.append(new_n)
				edges[n] = [new_n]
			if n % 6 == 4:
				new_n = (n - 1) // 3
				if new_n not in nodes:
					nodes.append(new_n)
					edges[n].append(new_n)

	g = Digraph(
		graph_attr={'nodesep': '0.1', 'ranksep': '0.3'},
		node_attr={'style': 'filled,setlinewidth(0.5)', 'fontname': 'consolas'}
	)

	for n in nodes:
		g.node(str(n), label=str(n), shape='oval', fillcolor='#30e090' if n == 1 else '#80c0ff')

	for dest_node, src_nodes in edges.items():
		for src_node in src_nodes:
			g.edge(str(src_node), str(dest_node))

	g.render('trajectory_graph', view=True, cleanup=True, format='png')
