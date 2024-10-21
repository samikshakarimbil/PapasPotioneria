create table
  public.global_inventory (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    num_green_potions integer null default 0,
    num_green_ml integer null default 0,
    gold integer null default 100,
    num_red_potions integer null default 0,
    num_red_ml integer null default 0,
    num_blue_potions integer null default 0,
    num_blue_ml integer null default 0,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.potions (
    id bigint generated by default as identity not null,
    red_amt integer null default 0,
    green_amt integer null default 0,
    blue_amt integer null,
    dark_amt integer null default 0,
    inventory integer null default 0,
    price integer null default 0,
    sku text null default '""'::text,
    constraint potions_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.carts (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    customer text null,
    class text null,
    level integer null,
    constraint carts_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.cart_items (
    id bigint generated by default as identity not null,
    cart_id bigint null,
    potion_id bigint null,
    quantity integer null,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id),
    constraint cart_items_potion_id_fkey foreign key (potion_id) references potions (id)
  ) tablespace pg_default;