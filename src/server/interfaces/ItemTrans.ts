  
  export default interface ItemTrans {
    spaceId: number;
    itemId: number;
    name: string;
    colorCode: string;
    imgPath: string;
    tags: string;
    description: string;
    category: string;
    reminderDtm: Date;
    reminderComplete: boolean;
  }
  