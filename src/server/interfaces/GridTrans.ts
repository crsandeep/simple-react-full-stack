
export default interface GridTrans {
  spaceId: number;

  // for display
  tagsMap: Map<string, string[]>;

  // for batch display/insert/update
  layouts: any[];

  gridId: number; // for delete only
}
