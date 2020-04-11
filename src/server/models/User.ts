import {Table, Column, Model, CreatedAt, UpdatedAt, DataType, AutoIncrement, PrimaryKey, Unique, AllowNull, Index, HasMany} from 'sequelize-typescript';
import Space from './Space';
 
@Table
export default class User extends Model<User> {
  @Index
  @AutoIncrement
  @PrimaryKey
  @Unique
  @Column(DataType.INTEGER)
  userId: number;

  @AllowNull(false)
  @Column(DataType.TEXT)
  name: string;
  
  @AllowNull(false)
  @Column(DataType.TEXT)
  email: string;
  
  @AllowNull(true)
  @Column(DataType.TEXT)
  password: string;
  
  @HasMany(() => Space)
  spaces: Space[];

  @CreatedAt
  creationDate: Date;
 
  @UpdatedAt
  updatedOn: Date;
}