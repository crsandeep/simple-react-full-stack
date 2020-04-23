import {Table, Column, Model, CreatedAt, UpdatedAt, DataType, AutoIncrement, PrimaryKey, Unique, AllowNull, Index, HasMany, ForeignKey, BelongsTo} from 'sequelize-typescript';
import Item from './Item';
import Space from './Space';

@Table
export default class Grid extends Model<Grid> {
  @Index
  @AutoIncrement
  @PrimaryKey
  @Unique
  @Column(DataType.INTEGER)
  gridId: number;

  @AllowNull(false)
  @Column(DataType.TEXT)
  name: string;
  
  @HasMany(() => Item)
  items: Item[];

  //relationship with other tables
  @ForeignKey(() => Space)
  @AllowNull(false)
  @Column(DataType.INTEGER)
  spaceId: number;
  
  @BelongsTo(() => Space)
  Space: Space;

  @CreatedAt
  creationDate: Date;
 
  @UpdatedAt
  updatedOn: Date;
}