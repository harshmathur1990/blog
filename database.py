from sqlalchemy import create_engine, MetaData

engine = create_engine(
    'mysql+pymysql://root:root@localhost/blog',
    convert_unicode=True, pool_size=20)
metadata = MetaData()