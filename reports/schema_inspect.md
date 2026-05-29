# 4 号 JSON Schema 扫描报告

## 总览

| 账号 | 文章数 | 评论数 | 文章字段数 | 评论字段数 |
|---|---|---|---|---|
| kazik | 673 | 66570 | 52 | 30 |
| baoyu | 813 | 3040 | 52 | 29 |
| saiboshanxin | 897 | 14957 | 53 | 31 |
| huashu | 398 | 4328 | 53 | 30 |

## 文章级字段:4 号覆盖对比

| 字段 | kazik | baoyu | saiboshanxin | huashu | 类型 | 样例(kazik 优先) |
|---|---|---|---|---|---|---|
| _accountName | 100.0% | 100.0% | 100.0% | 100.0% | str | `数字生命卡兹克` |
| _status | 100.0% | 100.0% | 100.0% | 100.0% | str | `正常` |
| aid | 100.0% | 100.0% | 100.0% | 100.0% | str | `2647657627_1` |
| album_id | 100.0% | 100.0% | 100.0% | 100.0% | str | `0` |
| appmsg_album_infos | 100.0% | 100.0% | 100.0% | 100.0% | list[empty]/list[object] | `[{"id": "3583569696974651393", "title": "AI绘图", "album_id": 3583569696974651400,...` |
| appmsgid | 100.0% | 100.0% | 100.0% | 100.0% | int | `2647657627` |
| audio_info | 3.7% | 0.4% | 2.5% | 0.3% | object | `{"audio_infos": [{"audio_id": "MzIyMzA5NjEyMF8yNjQ3NjU4MzUz", "title": "卡兹克", "p...` |
| author_name | 100.0% | 100.0% | 100.0% | 100.0% | str | `卡兹克` |
| ban_flag | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| can_location_page_show | 5.1% | 48.6% | 24.7% | 16.3% | int | `0` |
| checking | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| commentNum | 100.0% | 100.0% | 99.2% | 100.0% | int | `19` |
| comments | 100.0% | 100.0% | 100.0% | 100.0% | list[empty]/list[object] | `[{"author_like_status": 0, "bizattr_servicetype": 0, "can_share": true, "content...` |
| content | 100.0% | 100.0% | 100.0% | 100.0% | str | `关于ChatGPT的兄弟 - AI绘图的小思考  最近ChatGPT和人工智能上了天，不管是资本市场还是大众舆论，无不是最火热的话题，就连背后的某些算力公司，都...` |
| copyright_stat | 100.0% | 100.0% | 100.0% | 100.0% | int | `1` |
| copyright_type | 100.0% | 100.0% | 100.0% | 100.0% | int | `1` |
| cover | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURraibxGuHz6cfRAR74OFy6ib8ORSRRyPOu5Jibi...` |
| cover_img | 87.1% | 71.5% | 71.8% | 69.3% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURrIcXBTiag1o1wbqvvIqWmk19HsAibUnqYnzmdi...` |
| cover_img_3_4 | 0.4% | 20.9% | 13.3% | 19.8% | str | `http://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURrNcyOB2ErrMDR7uXe3wvjIP0stFRej5Gv2d6sts...` |
| cover_img_first | 0.4% | 20.9% | 13.3% | 19.8% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURrNcyOB2ErrMDR7uXe3wvjIvOOvUUpsNJ4u4MY5...` |
| cover_img_theme_color | 87.1% | 71.5% | 71.8% | 69.3% | object | `{"r": 9, "g": 16, "b": 26}` |
| create_time | 100.0% | 100.0% | 100.0% | 100.0% | int | `1677321528` |
| digest | 100.0% | 100.0% | 100.0% | 100.0% | str | `要成长为新的物种，就要经历所有你不会再扮演的角色。` |
| duration | — | 7.1% | 0.9% | 2.5% | int | `78` |
| fakeid | 100.0% | 100.0% | 100.0% | 100.0% | str | `MzIyMzA5NjEyMA==` |
| has_red_packet_cover | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| img_3_4_theme_color | 0.3% | 20.9% | 10.0% | 13.3% | object | `{"r": 160, "g": 160, "b": 160}` |
| img_first_theme_color | 0.4% | 20.9% | 13.3% | 19.8% | object | `{"r": 159, "g": 159, "b": 159}` |
| is_deleted | 100.0% | 100.0% | 100.0% | 100.0% | bool | `False` |
| is_pay_subscribe | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| is_rumor_refutation | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| is_user_title | 4.8% | — | 1.7% | 4.3% | int | `1` |
| item_show_type | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| itemidx | 100.0% | 100.0% | 100.0% | 100.0% | int | `1` |
| likeNum | 100.0% | 100.0% | 99.2% | 100.0% | int | `11` |
| line_info | 100.0% | 100.0% | 100.0% | 100.0% | object | `{"use_line": 1, "line_count": 11, "is_appmsg_flag": 1, "is_use_flag": 0}` |
| link | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://mp.weixin.qq.com/s/d7I1zP7rvXZkeq3ct93FEg` |
| location_page_show | 5.1% | 48.6% | 24.7% | 16.3% | int | `0` |
| media_duration | 100.0% | 100.0% | 100.0% | 100.0% | str | `0:00` |
| mediaapi_publish_status | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| multi_picture_cover | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| oldLikeNum | 100.0% | 100.0% | 99.2% | 100.0% | int | `46` |
| pay_album_info | 100.0% | 100.0% | 100.0% | 100.0% | object | `{"appmsg_album_infos": []}` |
| pic_cdn_url_16_9 | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURraibxGuHz6cfRAR74OFy6ib8R47Z9JBicz8908...` |
| pic_cdn_url_1_1 | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURraibxGuHz6cfRAR74OFy6ib8ORSRRyPOu5Jibi...` |
| pic_cdn_url_235_1 | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURraibxGuHz6cfRAR74OFy6ib8R47Z9JBicz8908...` |
| pic_cdn_url_3_4 | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURrNcyOB2ErrMDR7uXe3wvjIP0stFRej5Gv2d6st...` |
| readNum | 100.0% | 100.0% | 99.2% | 100.0% | int | `3086` |
| shareNum | 100.0% | 100.0% | 99.2% | 100.0% | int | `53` |
| share_imageinfo | 100.0% | 100.0% | 100.0% | 100.0% | list[empty]/list[object] | `[{"file_id": 500175405, "cdn_url": "https://mmbiz.qpic.cn/mmbiz_jpg/OjgKEXmLURrN...` |
| tagid | 100.0% | 100.0% | 100.0% | 100.0% | list[empty] |  |
| title | 100.0% | 100.0% | 100.0% | 100.0% | str | `关于ChatGPT的兄弟 - AI绘图的小思考` |
| update_time | 100.0% | 100.0% | 100.0% | 100.0% | int | `1677321528` |

## 评论级字段:4 号覆盖对比

| 字段 | kazik | baoyu | saiboshanxin | huashu | 类型 | 样例 |
|---|---|---|---|---|---|---|
| $reply_list | 100.0% | 100.0% | 100.0% | 100.0% | list[empty]/list[object] | `[{"author_like_status": 0, "bizattr_servicetype": 1, "can_share": true, "content...` |
| author_like_status | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| bizattr_servicetype | 99.8% | 100.0% | 99.9% | 100.0% | int | `0` |
| can_share | 100.0% | 100.0% | 100.0% | 100.0% | bool | `True` |
| content | 100.0% | 100.0% | 100.0% | 100.0% | str | `年底特来考古！` |
| content_id | 100.0% | 100.0% | 100.0% | 100.0% | str | `7226923370539909453` |
| create_time | 100.0% | 100.0% | 100.0% | 100.0% | int | `1703841446` |
| dislike_status | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| highlight | 0.0% | — | 0.0% | 1.5% | object | `{"highlight_pos": [75], "s1s_context_info": ["%7B%22mixerCommonContext%22%3A%22%...` |
| id | 100.0% | 100.0% | 100.0% | 100.0% | int | `2` |
| identity_name | 99.8% | 100.0% | 99.9% | 100.0% | str | `oOIscwM2AZtaKN9baqVkar0ng-ak` |
| identity_type | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| ip_wording | 100.0% | 100.0% | 100.0% | 100.0% | object | `{"city_id": "", "city_name": "", "country_id": "156", "country_name": "中国", "pro...` |
| is_can_delete | 100.0% | 100.0% | 100.0% | 100.0% | bool | `False` |
| is_elected | 100.0% | 100.0% | 100.0% | 100.0% | int | `1` |
| is_from | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| is_from_friend | 100.0% | 100.0% | 100.0% | 100.0% | int | `1` |
| is_from_me | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| is_reward | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| is_top | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| like_num | 100.0% | 100.0% | 100.0% | 100.0% | int | `15` |
| like_status | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| logo_url | 100.0% | 100.0% | 100.0% | 100.0% | str | `https://wx.qlogo.cn/mmopen/2jjfQoZLoqULzBbB1YhS9AD77YHDAfS0ST5BLjQ3jzyzWANJLBSy6...` |
| multi_info | 100.0% | 100.0% | 100.0% | 100.0% | object | `{"emojis": [], "pictures": []}` |
| my_id | 100.0% | 100.0% | 100.0% | 100.0% | int | `333` |
| need_show_publish_tips | 100.0% | 100.0% | 100.0% | 100.0% | bool | `False` |
| nick_name | 100.0% | 100.0% | 100.0% | 100.0% | str | `枫丝语` |
| openid | 100.0% | 100.0% | 100.0% | 100.0% | str | `oOIscwM2AZtaKN9baqVkar0ng-ak` |
| party_flag | 100.0% | 100.0% | 100.0% | 100.0% | int | `0` |
| quote_info | — | — | 0.0% | — | object | `{"quote_items": [{"begin_offset": 2, "end_offset": 4, "pic_index": 1, "pic_url":...` |
| reply_new | 100.0% | 100.0% | 100.0% | 100.0% | object | `{"max_reply_id": 1, "reply_list": [], "reply_total_cnt": 0}` |