drop table if exists acc_links;
create table acc_links (
    id integer primary key autoincrement,
    bnet_id integer not null,
    reddit_id varchar not null,
    last_update date not null,
    last_rank integer not null
);
