import React from 'react';
import { shallow, mount } from 'enzyme';
import ConnectedApp, {Item} from '../../src/client/views/Item';
import ItemComp from '../../src/client/components/ItemComp';
import * as Constants from '../../src/client/constants/Item';

const itemId = 99;
const name = 'Test Name';
const mode = Constants.FORM_EDIT_MODE;
const colorCode = 'Test Yellow';
const tags= 'Test Winter';
const description = 'Test description';
const category = 'Test Bedroom 1';
const reminderDtm = new Date();


describe('Test Components', () => {
  const props = {
    editStatus: { isSuccess: null, data: null, message: null, operation:null },
    item: {
        itemId: itemId,
        name: name,
        colorCode: colorCode,
        imageUrl: null,
        imgFile: null,
        imgDisplayUrl: null,
        tags: tags,
        description: description,
        category: category,
        reminderDtm: reminderDtm,
    },
    formState: {
      formMode: mode,
      pageLoading:false,
      name: name,
      colorCode: colorCode,
      imageUrl: '',
      imgFile: null,
      imgDisplayUrl: '',
      tags: tags,
      description: description,
      category: category,
      reminderDtm: reminderDtm,
    },
    itemList: [],
    sagaGetItemList:jest.fn(),
    sagaUpdateItem:jest.fn(),
    sagaAddItem:jest.fn(),
    sagaDeleteItem:jest.fn(),
    sagaGetItem:jest.fn(),
    sagaRemoveItemImg:jest.fn(),
    updateFormMode:jest.fn(),

    handleFormSave:jest.fn(),
    handleCancel:jest.fn(),
    handleNew:jest.fn(),
    handleEdit:jest.fn(),
    handleDelete:jest.fn(),
    handleReloadList:jest.fn(),
    handleRemoveItemImg:jest.fn(),
  }
  
  it('Should render view and components',()=>{
    const view = shallow(<Item {...props}/>);
    expect(view).toHaveLength(1);

    const comp = view.find('ItemComp');
    expect(comp).toHaveLength(1);

    const compProps = comp.props();
    // expect(compProps).toHaveProperty('item', props.item);
    expect(compProps).toHaveProperty('itemList',props.itemList);
    expect(compProps).toHaveProperty('editStatus', props.editStatus);
    expect(compProps).toHaveProperty('formState', props.formState);
  });

  it('Should render components with details (Read only mode)',()=>{
    let cloneProps = Object.assign({}, props);
    cloneProps.formState.formMode = Constants.FORM_READONLY_MODE;
    
    const comp = shallow(<ItemComp {...cloneProps}/>);
    expect(comp).toHaveLength(1);
    
    //before list
    expect(comp.find('Button')).toHaveLength(4);
    expect(comp.find('Button').first().text()).toEqual('New Item');

    //modal
    const modal = comp.find('Bootstrap(Modal)');
    expect(modal).toHaveLength(1);
    expect(modal.find('ModalTitle').text()).toEqual('Item Details');
    expect(modal.find('ModalBody').find('Formik')).toHaveLength(1);
    expect(modal.find('ModalFooter').find('Button')).toHaveLength(2);
  });

  it('Should render components with details(Edit Mode)',()=>{
    let cloneProps = Object.assign({}, props);
    cloneProps.formState.formMode = Constants.FORM_EDIT_MODE;

    const comp = shallow(<ItemComp {...cloneProps}/>);
    expect(comp).toHaveLength(1);
    
    //before list
    expect(comp.find('Button')).toHaveLength(3);
    expect(comp.find('Button').first().text()).toEqual('Refresh');

    //modal
    const modal = comp.find('Bootstrap(Modal)');
    expect(modal).toHaveLength(1);
    expect(modal.find('ModalTitle').text()).toEqual('Item Details');
    expect(modal.find('ModalBody').find('Formik')).toHaveLength(1);
    expect(modal.find('ModalFooter').find('Button')).toHaveLength(2);
    // console.log(comp.debug());
  });


  // it('Should render form component',()=>{
  //   let cloneProps = Object.assign({}, props);
  //   cloneProps.formState.formMode = Constants.FORM_EDIT_MODE;


  //   const comp = mount(<ItemComp {...cloneProps}/>);
  //   expect(comp).toHaveLength(1);
    
  //   //before list
  //   expect(comp.find('Button')).toHaveLength(3);
  //   expect(comp.find('Button').first().text()).toEqual('Refresh');

  //   //form
  //   const form = comp.find('Formik');
  //   expect(form.find('Row')).toHaveLength(6);
  //   expect(form.find('Row').at(1).find('label').text()).toEqual('Name');
  //   expect(form.find('Row').last().find('label').text()).toEqual('Reminder');

  // });
});

