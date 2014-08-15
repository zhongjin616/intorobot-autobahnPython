drop table robot_datastreams;
drop table robot_commandstreams;
drop table robot_videos;
drop table robot_images;


--create tables to store robot data
create table robot_datastreams (
    feed_id varchar(32) not null,
    id serial primary key, 
    stream_id varchar(30) not null, 
    updated_at TIMESTAMP not null, 
    current_value real not null 
);

create table robot_commandstreams (
    feed_id varchar(32) not null,
    id serial primary key,
    stream_id varchar(30) not null, 
    updated_at TIMESTAMP not null,
    current_value real not null
);

create table robot_images(
    feed_id varchar(32) not null, 
    id serial primary key, 
    taken_time TIMESTAMP not null,
    raster OID not null
);

create table robot_videos(
    feed_id varchar(32) not null,
    id serial primary key,
    taken_time TIMESTAMP, 
    raster OID not null
);

