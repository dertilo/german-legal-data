from time import sleep, time

from esutil.es_parallel_bulk import populate_es_parallel_bulk
from esutil.es_util import build_es_client

if __name__ == "__main__":
    INDEX_NAME = "bverfg"
    TYPE = "decision"
    es = build_es_client()

    es.indices.delete(index=INDEX_NAME, ignore=[400, 404])
    es.indices.create(index=INDEX_NAME, ignore=400)
    sleep(3)

    files = ["BverfG.jsonl.gz"]

    start = time()
    populate_es_parallel_bulk(es, files, INDEX_NAME, TYPE)
    dur = time() - start

    sleep(3)
    count = es.count(
        index=INDEX_NAME, doc_type=TYPE, body={"query": {"match_all": {}}}
    )["count"]
    print("populating es-index with %d documents took: %0.2f seconds" % (count, dur))

'''
populating es-index with 16197 documents took: 10.25 seconds
'''