import {Table, Column, Model, CreatedAt, UpdatedAt, DataType, AutoIncrement, PrimaryKey, Unique, AllowNull, Index, HasMany} from 'sequelize-typescript';
import Item from './Item';
 
@Table
export default class Space extends Model<Space> {
  @Index
  @AutoIncrement
  @PrimaryKey
  @Unique
  @Column(DataType.INTEGER)
  spaceId: number;

  @AllowNull(false)
  @Column(DataType.TEXT)
  name: string;
  
  @AllowNull(true)
  @Column(DataType.TEXT)
  colorCode: string;
  
  @AllowNull(true)
  @Column(DataType.TEXT)
  imgPath: string;
  
  @AllowNull(true)
  @Column(DataType.TEXT)
  tags: string;
  
  @AllowNull(true)
  @Column(DataType.TEXT)
  location: string;
  
  @AllowNull(true)
  @Column(DataType.INTEGER)
  sizeUnit: number;
  
  @AllowNull(true)
  @Column(DataType.INTEGER)
  sizeWidth: number;
  
  @AllowNull(true)
  @Column(DataType.INTEGER)
  sizeHeight: number;
  
  @AllowNull(true)
  @Column(DataType.INTEGER)
  sizeDepth: number;
 
  @HasMany(() => Item)
  items: Item[];

  @CreatedAt
  creationDate: Date;
 
  @UpdatedAt
  updatedOn: Date;
}