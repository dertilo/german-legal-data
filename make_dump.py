from elasticsearch.helpers import scan
from tqdm import tqdm
from util import data_io

from esutil.es_util import build_es_client


def elastic_scan(
    es_client,
    index,
    query,  # {"_source":["id","name","content.features"]},
    batch_size=100,
    scroll_timeout="1m",
    limit=None,
):
    scan_iterator = scan(
        es_client, query=query, index=index, scroll=scroll_timeout, size=batch_size
    )
    for counter, hit in enumerate(scan_iterator):
        if limit is not None and counter > limit:
            break
        yield hit


def process(d):
    # d = {k:d[k] for k in ['date','aktenzeichen','zitiervorschlag','entscheidungsdatum','content']}
    return d


if __name__ == "__main__":
    es_client = build_es_client()
    TYPE = "decision"
    INDEX = "juris"
    # fmt: off
    fields = ["Orientierungssatz", "Gründe", "Tenor", "Leitsatz",
                 "Sonstiger Orientierungssatz", "Abweichende Meinung",
                 "Entscheidungsgründe", "Tatbestand", "Sonstiger Kurztext",
                 "Sonstiger Langtext"]
    # fmt: on

    body = {"query": {"multi_match": {"query": "185 StGB", "fields": fields}}}
    hits_g = elastic_scan(
        es_client, index=INDEX, query=body, batch_size=100,
    )
    docs = (process(d["_source"]) for d in tqdm(hits_g))

    # docs = (process(d) for d in data_io.read_jsonl('BverfG_juris.jsonl.gz'))
    data_io.write_jsonl("decisions_185_StGB.jsonl.gz", docs)
