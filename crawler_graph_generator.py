import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from collections import deque
import sys

# === CONFIGURATION ===
DEFAULT_ROOT_URL = 'http://158.101.167.252'
DEFAULT_MAX_PAGES = 50

visited_pages = set()
seen_urls = set()
nodes = {}
edges = []
edge_set = set()


def is_a_file(url):
    endings = ['.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.tar.gz', '.rar', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.avi', '.mov',".apk", ".mkv", ".webm", ".flv", ".wmv", ".txt", ".csv", ".json", ".xml"]
    return any(url.endswith(ext) for ext in endings)


def normalize_url(url):
    """Clean URL: remove fragments, query params, trailing slashes"""
    return url.split('#')[0].split('?')[0].rstrip('/')

def get_label(url):
    """Get the last part of the URL path to use as label"""
    path = urlparse(url).path.rstrip('/')
    if path in ['', '/']:
        return '/'
    return path.split('/')[-1]

def is_internal(link, root_domain):
    """Determine whether a link is internal to the site"""
    parsed = urlparse(link)
    return parsed.netloc in ['', root_domain]

def is_direct_parent(child_url, target_url):
    """Check if target_url is the parent directory of child_url"""
    child_path = urlparse(child_url).path.rstrip('/')
    target_path = urlparse(target_url).path.rstrip('/')

    if '/' not in child_path:
        return False

    parent_path = '/'.join(child_path.split('/')[:-1])
    return parent_path == target_path

def add_node(url, root_domain):
    """Add a node to the graph with proper label and color"""
    if url not in nodes:
        node = {
            "id": url,
            "label": get_label(url)
        }
        if not is_internal(url, root_domain):
            node["color"] = "#ccc"
            node["label"] = node["id"]
        nodes[url] = node

def add_edge(from_url, to_url):
    """Add a directional edge between two URLs if it doesn't already exist"""
    edge_key = (from_url, to_url)
    if edge_key not in edge_set:
        edges.append({"from": from_url, "to": to_url, "arrows": "to"})
        edge_set.add(edge_key)

def crawl_page(url, root_domain, ROOT_URL):
    """Extract links from a single page (non-recursive)"""
    visited_pages.add(url)
    add_node(url, root_domain)

    try:
        response = requests.get(url, timeout=10)
        if not response.ok:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        found_links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_link = normalize_url(urljoin(url, href))

            if full_link == url:
                continue
                
            if is_direct_parent(url, full_link):
                continue

            if full_link in seen_urls:
                continue

            if full_link.split("/")[-1] == "main":
                full_link = "/".join(full_link.split("/")[:-1])


            if full_link == ROOT_URL:
                continue

            add_node(full_link, root_domain)
            add_edge(url, full_link)
            

            if is_a_file(full_link):
                continue

            if is_internal(full_link, root_domain):
                found_links.append(full_link)

        seen_urls.update(found_links)  
        return found_links

    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return []

def crawl_bfs(ROOT_URL, root_domain, MAX_PAGES):
    """Breadth-first search crawling using a queue"""
    queue = deque([ROOT_URL])
    
    while queue and len(visited_pages) < MAX_PAGES:
        current_url = queue.popleft()  # Get next URL from front of queue
        
        if current_url in visited_pages:
            continue
            
        # Crawl current page and get all links found
        found_links = crawl_page(current_url, root_domain, ROOT_URL)
        
        # Add new unvisited links to the back of the queue
        for link in found_links:
            if link not in visited_pages and link not in queue:
                queue.append(link)
        
        print(f"Queue size: {len(queue)}, Visited: {len(visited_pages)} URLs")

def main(ROOT_URL=DEFAULT_ROOT_URL, MAX_PAGES=DEFAULT_MAX_PAGES,file_name="graph"):
    root_domain = urlparse(ROOT_URL).netloc
    crawl_bfs(ROOT_URL, root_domain, MAX_PAGES)

    # Ensure root label is "/"
    if ROOT_URL in nodes:
        nodes[ROOT_URL]["label"] = "/"

    graph_data = {
        "nodes": list(nodes.values()),
        "edges": edges
    }

    with open(f"{file_name}.json", "w") as f:
        json.dump(graph_data, f, indent=2)

    print("✅ graph.json created")

if __name__ == "__main__":
    #get the arguments from the command line

    if len(sys.argv) > 1:
        ROOT_URL = sys.argv[1]
        MAX_PAGES = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAX_PAGES
        FILENAME = sys.argv[3] if len(sys.argv) > 3 else "graph"
        print(f"Using ROOT_URL: {ROOT_URL} and MAX_PAGES: {MAX_PAGES}")
        main(ROOT_URL=ROOT_URL, MAX_PAGES=MAX_PAGES, file_name=FILENAME)

    else:
        main()