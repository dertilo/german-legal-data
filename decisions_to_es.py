import json
import os
from datetime import datetime
from time import time

from bs4 import BeautifulSoup

from esutil.es_stateful_parallel_pool import populate_es_parallel_pool, setup_index
from esutil.es_util import build_es_client


def parse_content(d: dict):
    def get_label(h):
        label = json.loads(h.find("h4").attrs["data-juris-toc"])["label"]
        return label

    def get_paragraphs(h):
        if h is not None:
            paragraphs = [
                p.text for p in h.find_all("dl", class_="RspDL") if len(p.text) > 0
            ]
        else:
            paragraphs = None
        return paragraphs

    def parse_key_value(topmore):
        try:
            key = get_label(topmore)
            value = get_paragraphs(topmore.next_sibling)
            return key, value
        except:
            return None

    # --------------------------------------------------------------------------------
    soup = BeautifulSoup(d["content"], "html.parser")

    kvs = [
        parse_key_value(topmore)
        for topmore in soup.find_all("div", class_="docLayoutMarginTopMore")
    ]

    parsed = {kv[0]: kv[1] for kv in kvs if kv is not None}
    d.update(parsed)
    try:
        d["date"] = datetime.strptime(d["date"], "%d.%m.%Y").isoformat()
    except:
        pass
    return d


if __name__ == "__main__":
    from pathlib import Path

    home = str(Path.home())

    data_path = home + "/data/juris/htmls"
    files = [data_path + "/" + f for f in os.listdir(data_path) if "hits" not in f]

    INDEX_NAME = "juris"
    TYPE = "decision"

    mapping = """
    {
      "mappings": {
        "properties": {
          "content": {
            "type": "str",
            "enabled": false
          }
        }
      }
    }
    """
    es_client = build_es_client()
    files = setup_index(es_client, files, INDEX_NAME, TYPE, from_scratch=False, mapping=mapping)
    start = time()
    num_processes = 8
    populate_es_parallel_pool(
        files, INDEX_NAME, TYPE, process_fun=parse_content, num_processes=num_processes
    )
    dur = time() - start
    print('took: %0.2f seconds'%dur)

    """
    using 'populate_es_streaming_bulk'-method
    461001it [5:38:14, 28.62it/s]
    kibana says indexing-rate around 23/s
    
    using 'populate_es_parallel_pool'-method with 8 processes:
    indexing-rate: 130/s
    1.3 mio docs took 3 hours
    """
