import React from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';
import {
  ListItemSecondaryAction,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  IconButton,
  ListItemAvatar,
  Avatar,
  Typography
} from '@material-ui/core/';
import { Badge } from 'react-bootstrap';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import CardGiftcardIcon from '@material-ui/icons/CardGiftcard';
import MenuBookIcon from '@material-ui/icons/MenuBook';
import BuildIcon from '@material-ui/icons/Build';
import EmojiEventsIcon from '@material-ui/icons/EmojiEvents';
import FavoriteBorderIcon from '@material-ui/icons/FavoriteBorder';
import FlightIcon from '@material-ui/icons/Flight';
import RestaurantIcon from '@material-ui/icons/Restaurant';
import KitchenIcon from '@material-ui/icons/Kitchen';
import HelpOutlineIcon from '@material-ui/icons/HelpOutline';
import ChildFriendlyIcon from '@material-ui/icons/ChildFriendly';
import Link from '@material-ui/core/Link';
import RemindNoteComp from './RemindNoteComp';


// generate item content in list view

const genListData = (itemList, isShowLocation, handleEdit, handleDelete) => {
  if (itemList == null) return;
  const elementList = [];

  for (const item of itemList) {
    let tagsArr = [];
    if (item.tags != null && item.tags.length > 0) {
      tagsArr = item.tags.split(',');
    }

    elementList.push(
      <ListItem
        key={item.itemId}
        alignItems="flex-start"
        button
      >
        <ListItemAvatar>
          {item.imgPath != null ? (
            <Avatar variant="rounded" alt={item.name} src={item.imgPath} />
          ) : (
            <Avatar variant="rounded" alt={item.name}>
              {
                item.name.substring(0, 4)
              }
            </Avatar>
          )}
        </ListItemAvatar>
        <ListItemText
          primary={item.name}
          secondary={(
            <React.Fragment>
              <Typography
                component="span"
                variant="body2"
                className="spaceList-inline"
                color="textSecondary"
              >
                {item.description}
                {
                  item.description != null && tagsArr != null && tagsArr.length > 0
                    ? (<br />) : null
                }
                {
                  tagsArr.map(tag => (
                    <Badge key={tag} variant="warning">
                      {tag}
                    </Badge>
                  ))
                }
              </Typography>
              {
                item.description != null || (tagsArr != null && tagsArr.length > 0)
                  ? (<br />) : null
              }
              {/* //reminder */}
              <RemindNoteComp remindDtm={item.reminderDtm} />
              {
                item.reminderDtm != null
                  ? (<br />) : null
              }

              {/* // ignore breadcrumbs as it triger ol cannot appear as a descendant of p tag issue */}
              {isShowLocation === true ? (
                <div>
                  <Link color="inherit" href="/space">
                    <i className="fa fa-fw fa-home" style={{ fontSize: '1.05em' }} />
                    {
                      // show space name
                      `${item.spaceLocation} - ${item.spaceName}`
                    }
                  </Link>
                  <span>{' > '}</span>
                  <Link color="inherit" href="/grid">
                    <i className="fa fa-fw fa-table" style={{ fontSize: '1.05em' }} />
                    {
                        // show location with grid ID with 2 digits
                        item.gridId.toString().padStart(2, '0').slice(-3)
                      }
                  </Link>
                </div>
              ) : null}
            </React.Fragment>
          )}
        />
        <ListItemSecondaryAction>
          <IconButton aria-label="edit" onClick={() => handleEdit(item.itemId)}>
            <EditIcon />
          </IconButton>
          <IconButton aria-label="delete" onClick={() => handleDelete(item.itemId, item.name, item.description)}>
            <DeleteIcon />
          </IconButton>
        </ListItemSecondaryAction>
      </ListItem>
    );
  }
  return elementList;
};


const genListView = (itemList, isShowLocation, handleEdit, handleDelete) => {
  const displayList = [];
  const itemMap = new Map();
  let tempList = null;

  // prepare Map<category,List<Item>> for further generation
  for (const item of itemList) {
    // get corresponding list
    if (itemMap.get(item.category) != null) {
      tempList = itemMap.get(item.category);
    } else {
      tempList = [];
    }

    // add to list
    tempList.push(item);

    // update map with latest list
    itemMap.set(item.category, tempList);
  }

  // generate header and related spaces under each location according to Map settings
  for (const [category, list] of itemMap) {
    displayList.push(
      <li key={`section-${category}`}>
        <ul className="spaceList-ul">
          <ListSubheader>
            {
              {
                Favorite: <FavoriteBorderIcon />,
                Travel: <FlightIcon />,
                Clothes: <i className="fas fa-tshirt" />,
                Shoes: <i className="fas fa-shoe-prints" />,
                Collections: <EmojiEventsIcon />,
                Baby: <ChildFriendlyIcon />,
                Books: <MenuBookIcon />,
                Gifts: <CardGiftcardIcon />,
                Food: <RestaurantIcon />,
                Kitchenware: <KitchenIcon />,
                Tools: <BuildIcon />,
                Others: <HelpOutlineIcon />
              }[category]
            }
            {' '}
            {category}
          </ListSubheader>
          {genListData(list, isShowLocation, handleEdit, handleDelete)}
        </ul>
      </li>
    );
  }
  return displayList;
};

function ItemListComp(props) {
  // generate item data
  const dataList = genListView(props.itemList, props.isShowLocation, props.handleEdit, props.handleDelete);

  return (
    <List className="spaceList-pc" subheader={<li />}>
      {dataList}
    </List>
  );
}

ItemListComp.defaultProps = {
  itemList: []
};

ItemListComp.propTypes = {
  itemList: PropTypes.arrayOf(PropTypes.object),
  handleEdit: PropTypes.func.isRequired,
  handleDelete: PropTypes.func.isRequired,
  isShowLocation: PropTypes.bool.isRequired
};

export default ItemListComp;
