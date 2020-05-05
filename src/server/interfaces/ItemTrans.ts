
export default interface ItemTrans {
    gridId: number;
    itemId: number;
    name: string;
    colorCode: string;
    imgPath: string;
    tags: string;
    description: string;
    category: string;
    reminderDtm: Date;
    reminderComplete: boolean;

    // other object attributes for display
    spaceName: string;
    spaceLocation: string;
}
