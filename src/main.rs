use std::collections::HashSet;
use std::io::{self, Read};

#[derive(Clone, Debug)]
struct Node {
    label: Option<usize>,
    children: Vec<usize>,
}

#[derive(Clone, Debug)]
struct Tree {
    nodes: Vec<Node>,
    root: usize,
    edges: Vec<(usize, usize)>,
    edge_of_child: Vec<Option<usize>>,
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
struct Component {
    leaves: Vec<usize>,
    newick: String,
}

type Forest = Vec<Component>;

fn main() {
    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .expect("failed to read stdin");

    match solve(&input) {
        Ok(forest) => {
            for component in forest {
                println!("{};", component.newick);
            }
        }
        Err(message) => {
            eprintln!("{message}");
            std::process::exit(1);
        }
    }
}

fn solve(input: &str) -> Result<Forest, String> {
    let mut trees = Vec::new();
    let mut leaf_count = None;

    for line in input.lines().map(str::trim).filter(|line| !line.is_empty()) {
        if let Some(rest) = line.strip_prefix("#p ") {
            let mut parts = rest.split_whitespace();
            let _tree_count = parts
                .next()
                .ok_or_else(|| "missing tree count in #p line".to_string())?;
            let n = parts
                .next()
                .ok_or_else(|| "missing leaf count in #p line".to_string())?
                .parse::<usize>()
                .map_err(|err| format!("invalid leaf count: {err}"))?;
            leaf_count = Some(n);
        } else if line.starts_with('#') {
            continue;
        } else {
            trees.push(parse_newick(line)?);
        }
    }

    let n = leaf_count.ok_or_else(|| "missing #p line".to_string())?;
    if trees.is_empty() {
        return Err("instance does not contain any trees".to_string());
    }

    if n > 20 {
        return Err(format!(
            "baseline exhaustive solver is intentionally capped at 20 leaves; instance has {n}"
        ));
    }

    let possible: Vec<HashSet<Forest>> = trees.iter().map(all_forests).collect();
    let first_tree = possible
        .first()
        .ok_or_else(|| "internal error: no generated forests".to_string())?;

    first_tree
        .iter()
        .filter(|forest| possible.iter().skip(1).all(|set| set.contains(*forest)))
        .min_by(|left, right| left.len().cmp(&right.len()).then_with(|| left.cmp(right)))
        .cloned()
        .ok_or_else(|| "no agreement forest found".to_string())
}

fn parse_newick(line: &str) -> Result<Tree, String> {
    let bytes = line.as_bytes();
    let mut parser = Parser {
        bytes,
        pos: 0,
        nodes: Vec::new(),
    };
    let root = parser.parse_subtree()?;
    parser.expect(b';')?;
    if parser.pos != bytes.len() {
        return Err(format!("unexpected trailing input at byte {}", parser.pos));
    }

    let mut tree = Tree {
        nodes: parser.nodes,
        root,
        edges: Vec::new(),
        edge_of_child: Vec::new(),
    };
    tree.edge_of_child = vec![None; tree.nodes.len()];
    collect_edges(root, &tree.nodes, &mut tree.edges, &mut tree.edge_of_child);
    Ok(tree)
}

struct Parser<'a> {
    bytes: &'a [u8],
    pos: usize,
    nodes: Vec<Node>,
}

impl Parser<'_> {
    fn parse_subtree(&mut self) -> Result<usize, String> {
        if self.peek() == Some(b'(') {
            self.pos += 1;
            let left = self.parse_subtree()?;
            self.expect(b',')?;
            let right = self.parse_subtree()?;
            self.expect(b')')?;
            self.push(Node {
                label: None,
                children: vec![left, right],
            })
        } else {
            let start = self.pos;
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
            if start == self.pos {
                return Err(format!("expected subtree at byte {}", self.pos));
            }
            let label = std::str::from_utf8(&self.bytes[start..self.pos])
                .map_err(|err| format!("invalid UTF-8 in label: {err}"))?
                .parse::<usize>()
                .map_err(|err| format!("invalid leaf label: {err}"))?;
            self.push(Node {
                label: Some(label),
                children: Vec::new(),
            })
        }
    }

    fn expect(&mut self, byte: u8) -> Result<(), String> {
        if self.peek() == Some(byte) {
            self.pos += 1;
            Ok(())
        } else {
            Err(format!("expected '{}' at byte {}", byte as char, self.pos))
        }
    }

    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.pos).copied()
    }

    fn push(&mut self, node: Node) -> Result<usize, String> {
        let index = self.nodes.len();
        self.nodes.push(node);
        Ok(index)
    }
}

fn collect_edges(
    node: usize,
    nodes: &[Node],
    edges: &mut Vec<(usize, usize)>,
    edge_of_child: &mut [Option<usize>],
) {
    for &child in &nodes[node].children {
        let edge_index = edges.len();
        edges.push((node, child));
        edge_of_child[child] = Some(edge_index);
        collect_edges(child, nodes, edges, edge_of_child);
    }
}

fn all_forests(tree: &Tree) -> HashSet<Forest> {
    let mut forests = HashSet::new();
    let edge_count = tree.edges.len();
    let masks = 1usize
        .checked_shl(edge_count as u32)
        .expect("too many edges for exhaustive enumeration");

    for mask in 0..masks {
        forests.insert(forest_for_mask(tree, mask));
    }

    forests
}

fn forest_for_mask(tree: &Tree, mask: usize) -> Forest {
    let mut roots = vec![tree.root];
    for (edge_index, &(_, child)) in tree.edges.iter().enumerate() {
        if is_cut(mask, edge_index) {
            roots.push(child);
        }
    }

    let mut forest = Vec::new();
    for root in roots {
        if let Some(component) = clean_component(tree, root, mask) {
            forest.push(component);
        }
    }
    forest.sort();
    forest
}

fn clean_component(tree: &Tree, node: usize, mask: usize) -> Option<Component> {
    if let Some(label) = tree.nodes[node].label {
        return Some(Component {
            leaves: vec![label],
            newick: label.to_string(),
        });
    }

    let mut children = Vec::new();
    for &child in &tree.nodes[node].children {
        let edge_index = tree.edge_of_child[child].expect("non-root child must have parent edge");
        if !is_cut(mask, edge_index) {
            if let Some(component) = clean_component(tree, child, mask) {
                children.push(component);
            }
        }
    }

    match children.len() {
        0 => None,
        1 => children.pop(),
        2 => {
            children.sort();
            let mut leaves = children[0].leaves.clone();
            leaves.extend(&children[1].leaves);
            leaves.sort_unstable();
            Some(Component {
                leaves,
                newick: format!("({},{})", children[0].newick, children[1].newick),
            })
        }
        _ => unreachable!("PACE trees are binary"),
    }
}

fn is_cut(mask: usize, edge_index: usize) -> bool {
    (mask & (1usize << edge_index)) != 0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn solves_official_tiny01_at_size_four() {
        let input = "#p 2 6\n(((5,6),(3,4)),(1,2));\n(((((4,2),1),5),3),6);\n";
        let forest = solve(input).unwrap();
        assert_eq!(forest.len(), 4);
    }

    #[test]
    fn solves_first_three_tiny_instances_at_known_sizes() {
        for (path, expected_size) in [
            ("data/instances/tiny/tiny01.nw", 4),
            ("data/instances/tiny/tiny02.nw", 1),
            ("data/instances/tiny/tiny03.nw", 7),
        ] {
            let input = std::fs::read_to_string(path).unwrap();
            let forest = solve(&input).unwrap();
            assert_eq!(forest.len(), expected_size, "{path}");
        }
    }
}
