trees = []
tree = []

for _ in range(n):
    line = sys.stdin.readline().strip()

    if line.lower() == "break":
        trees.append(tree)
        tree = []
    else:
        tree.append(list(map(int, line.split())))

if tree:
    trees.append(tree)

start, destination = map(int, sys.stdin.readline().split())

graph = defaultdict(list)
node_trees = defaultdict(set)

for tree_id, relations in enumerate(trees):
    for row in relations:
        parent = row[0]

        for child in row[1:]:
            node_trees[parent].add(tree_id)
            node_trees[child].add(tree_id)

            graph[(parent, tree_id)].append(((child, tree_id), 1))
            graph[(child, tree_id)].append(((parent, tree_id), 0))

for node, tree_ids in node_trees.items():
    for tree_id in tree_ids:
        for other_tree in tree_ids:
            if tree_id != other_tree:
                graph[(node, tree_id)].append(((node, other_tree), 1))

pq = []
dist = {}

for tree_id in node_trees[start]:
    state = (start, tree_id)
    dist[state] = 0
    heapq.heappush(pq, (0, state))

while pq:
    cost, state = heapq.heappop(pq)

    if cost != dist[state]:
        continue

    spot, tree_id = state

    if spot == destination:
        print(cost)
        return

    for next_state, energy in graph[state]:
        new_cost = cost + energy

        if new_cost < dist.get(next_state, float("inf")):
            dist[next_state] = new_cost
            heapq.heappush(pq, (new_cost, next_state))

print(-1)