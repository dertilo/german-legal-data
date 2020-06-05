import os

from tqdm import tqdm
from util import data_io
from whoosh import index
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import TEXT, ID, Schema
from whoosh.qparser import QueryParser, MultifieldParser


def build_index(data, schema, index_dir="indexdir"):

    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    ix = index.create_in(index_dir, schema)

    writer = ix.writer()
    for d in tqdm(data):
        writer.add_document(**d)
    writer.commit()


# fmt: off
FIELDS = ["Entscheidungsgründe","Abweichende Meinung","Tatbestand","Sonstiger Orientierungssatz","Leitsatz","Tenor","Gründe","Orientierungssatz","title","subtitle"]
# fmt: on


def process_field_name(f: str):
    return f.replace(" ", "_")


def build_schema_and_corpus():
    fields = {process_field_name(f): TEXT(stored=True, lang="de") for f in FIELDS}
    schema = Schema(aktenzeichen=ID(stored=True), **fields,)
    file = "BverfG.jsonl.gz"
    data = (
        {
            process_field_name(k): v
            for k, v in d.items()
            if k in FIELDS + ["aktenzeichen"]
        }
        for d in data_io.read_jsonl(file)
    )
    return schema, data


if __name__ == "__main__":

    INDEX_DIR = "bverfg_index"
    if not os.path.isdir(INDEX_DIR):
        schema, data = build_schema_and_corpus()
        build_index(data, schema, index_dir=INDEX_DIR)
        print("done building corpus")

    ix = index.open_dir(INDEX_DIR)

    with ix.searcher() as searcher:
        qp = MultifieldParser(FIELDS, schema=ix.schema)
        q = qp.parse("185 StGB")
        results = searcher.search(q, limit=None)

        data_io.write_jsonl("result.jsonl", (r.fields() for r in results))
