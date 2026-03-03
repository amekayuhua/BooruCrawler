import os
from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from core.models import ImageItem
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# 图片-标签 映射表
image_tag_table = Table(
    'image_tags', Base.metadata,
    Column('image_id', Integer, ForeignKey('images.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

# 图片-画师 映射表
image_artist_table = Table(
    'image_artists', Base.metadata,
    Column('image_id', Integer, ForeignKey('images.id', ondelete="CASCADE"), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id', ondelete="CASCADE"), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True) # 建立索引加速查询

class Artist(Base):
    __tablename__ = 'artists'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False)
    site = Column(String, nullable=False)
    file_url = Column(String)
    rating = Column(String)
    score = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    posted_at = Column(String)

    # 建立与 Tag 和 Artist 的多对多关系
    tags = relationship("Tag", secondary=image_tag_table, backref="images")
    artists = relationship("Artist", secondary=image_artist_table, backref="images")


class DBManager:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_or_create(self, session, model, **kwargs):
        """获取或创建记录：若不存在则新建"""
        with session.no_autoflush:
            instance = session.query(model).filter_by(**kwargs).first()
            if not instance:
                instance = model(**kwargs)
                session.add(instance)
            return instance

    def save_items(self, image_items: list[ImageItem]):
        """将爬取到的 ImageItem 列表存入数据库"""
        if not image_items:
            return

        session = self.Session()
        new_count = 0

        try:
            for item in image_items:
                # 去重：检查该网站的该 post_id 是否已存在
                exists = session.query(Image.id).filter_by(post_id=item.id, site=item.site).first()
                if exists:
                    continue

                new_image = Image(
                    post_id=item.id,
                    site=item.site,
                    file_url=item.url,
                    rating=item.rating,
                    score=int(item.score) if item.score else 0,
                    width=int(item.width) if item.width else 0,
                    height=int(item.height) if item.height else 0,
                    posted_at=item.created_at
                )

                # 处理画师（按逗号分割，去重）
                raw_artists = [a.strip() for a in item.artist.split(',')] if item.artist else ['Unknown']
                artist_names = list(set(raw_artists))
                
                for a_name in artist_names:
                    if a_name:
                        artist_obj = self._get_or_create(session, Artist, name=a_name)
                        new_image.artists.append(artist_obj)

                # 处理标签（按空格分割，去重）
                raw_tags = [t.strip() for t in item.tags.split(' ')] if item.tags else []
                tag_names = list(set(raw_tags))
                
                for t_name in tag_names:
                    if t_name:
                        tag_obj = self._get_or_create(session, Tag, name=t_name)
                        new_image.tags.append(tag_obj)

                session.add(new_image)
                new_count += 1

            session.commit()
            if new_count > 0:
                logger.info(f"成功保存 {new_count} 张新图片及其关系到数据库")
                
            else:
                logger.info(f"该批次没有新图片及其关系需要保存到数据库")
            
        except Exception as e:
            session.rollback()
            logger.error(f"数据库保存失败: {e}")
            
        finally:
            session.close()