select
    review_id,
    order_id,
    review_score,
    comment_title as review_comment_title,
    comment_message as review_comment_message,
    creation_date as review_creation_date,
    answer_timestamp as review_answer_timestamp
from {{ source('olist', 'order_reviews') }}
