import React from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import {
  ListItemSecondaryAction,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  IconButton,
  ListItemIcon,
  Avatar,
  Typography,
  useMediaQuery
} from '@material-ui/core/';


import { useTheme } from '@material-ui/core/styles';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faShoePrints, faTshirt, faHome, faTable
} from '@fortawesome/free-solid-svg-icons';
import { Badge } from 'react-bootstrap';
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
import Configs from '../config';


// generate item content in list view

const genListData = (itemList, isShowLocation, isReadOnly, handleEdit) => {
  if (itemList == null) return;
  const elementList = [];

  const theme = useTheme();
  const isLargeDevice = useMediaQuery(theme.breakpoints.up('sm'));
  const displayMaxNoTag = (isLargeDevice === true ? 9 : 3);

  for (const item of itemList) {
    let tagsArr = [];
    if (item.tags != null && item.tags.length > 0) {
      tagsArr = item.tags.split(',');
    }
    elementList.push(
      <ListItem
        key={item.itemId}
        alignItems="flex-start"
      >
        <ListItemIcon>
          {item.imgPath != null ? (
            <img
              src={`${Configs.BACKEND_SERVER_URL}/${item.imgPath}`}
              alt={item.name}
              className="spaceList-itemImage"
            />
          ) : (
            <Avatar variant="rounded" alt={item.name}>
              {
                item.name.substring(0, 4)
              }
            </Avatar>
          )}
        </ListItemIcon>
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
                  tagsArr.map((tag, i) => (
                    i <= displayMaxNoTag - 1 ? (
                      <Badge key={tag} variant="warning">
                        {tag}
                      </Badge>
                    ) : null
                  ))
                }
                {
                  tagsArr.length > displayMaxNoTag ? (
                    <Badge variant="warning">
                      {tagsArr.length - displayMaxNoTag}
                      {' '}
                      {' More'}
                    </Badge>
                  ) : null
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
                <span>
                  <Link color="inherit" href="/space">
                    <FontAwesomeIcon icon={faHome} style={{ fontSize: '1.05em' }} />
                    {
                      // show space name
                      `${item.spaceLocation} > ${item.spaceName}`
                    }
                  </Link>
                  <span>{' > '}</span>
                  <Link color="inherit" href="/grid">
                    <FontAwesomeIcon icon={faTable} style={{ fontSize: '1.05em' }} />
                    {
                        // show location with grid ID with 2 digits
                        item.gridId.toString().padStart(2, '0').slice(-3)
                      }
                  </Link>
                </span>
              ) : null}
            </React.Fragment>
          )}
        />
        {
          isReadOnly === true
            ? null : (
              <ListItemSecondaryAction>
                <IconButton aria-label="edit" onClick={() => handleEdit(item.itemId)} size="small">
                  <EditIcon />
                </IconButton>
              </ListItemSecondaryAction>
            )
          }
      </ListItem>
    );
  }
  return elementList;
};


const genListView = (itemList, isShowLocation, isReadOnly, handleEdit) => {
  const displayList = [];
  const itemMap = new Map();
  let tempList = null;

  if (itemList === null) return displayList;

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
                Clothes: <FontAwesomeIcon icon={faTshirt} />,
                Shoes: <FontAwesomeIcon icon={faShoePrints} />,
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
          {genListData(list, isShowLocation, isReadOnly, handleEdit)}
        </ul>
      </li>
    );
  }
  return displayList;
};

function ItemListComp(props) {
  // generate item data
  const dataList = genListView(props.itemList, props.isShowLocation, props.isReadOnly, props.handleEdit);

  return (
    <List className="spaceList-pc" subheader={<li />}>
      {dataList}
    </List>
  );
}

ItemListComp.defaultProps = {
  itemList: [],
  handleEdit(itemId) {}
};

ItemListComp.propTypes = {
  itemList: PropTypes.arrayOf(PropTypes.object),
  handleEdit: PropTypes.func,
  isShowLocation: PropTypes.bool.isRequired,
  isReadOnly: PropTypes.bool.isRequired
};

export default ItemListComp;
