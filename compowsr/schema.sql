drop table if exists acc_links;
create table acc_links (
    id integer primary key autoincrement,
    bnet_id text not null,
    reddit_id text not null,
    last_update date not null,
    last_rank integer not null
);

