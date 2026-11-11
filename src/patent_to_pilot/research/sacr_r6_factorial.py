"""R6 text-to-row binding into existing factorial ranking; no labels or encoding."""
from .sacr_r6_components import prepare_embedding
from .sacr_embedding import bind_embeddings
from .sacr_factorial import compare_factorial


def compare_r6(*,proposal,source,query_id,generic_views,configuration_sha256,
               vectors,embedding_receipt,expected_plan_sha256,expected_encoder_sha256,corpus):
    prepared=prepare_embedding(proposal,source=source,query_id=query_id,generic_views=generic_views,
                               configuration_sha256=configuration_sha256)
    plan=prepared['embedding_plan']
    matrix=bind_embeddings(plan,vectors,embedding_receipt,expected_plan_sha256=expected_plan_sha256,
                           expected_encoder_sha256=expected_encoder_sha256)
    components=matrix[plan['component_rows']]
    blocks=[components[block['start']:block['end']] for block in plan['component_blocks']]
    def views(kind):
        rows=plan['view_rows'][kind]
        return ['anchor',*[f'{kind}-{i}' for i in range(1,len(rows))]],matrix[rows]
    result=compare_factorial(**corpus,generic_views=views('generic'),invariant_views=views('selective'),
                             component_blocks=blocks)
    return {'factorial':result,'plan_sha256':plan['plan_sha256'],'encoder_sha256':expected_encoder_sha256,
            'configuration_sha256':configuration_sha256,'unique_encoded_rows':len(matrix),
            'compact_equals_anchor':prepared['compact_equals_anchor'],'semantic_pass':False}
