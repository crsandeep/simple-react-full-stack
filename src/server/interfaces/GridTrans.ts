
export default interface GridTrans {
  spaceId: number;

  // for batch display/insert/update
  layouts: any[];

  gridId: number; // for delete only

  imgPath: String; // for display only

}
